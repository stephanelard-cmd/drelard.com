"""Guardrails for the two medical explanations corrected after PR #2 review.

These checks protect the distinctions, not a frozen version of the prose.
Run with ``python3 -m unittest discover -s scripts -p 'test_*.py'``.
"""

from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata
import unittest


ROOT = Path(__file__).resolve().parents[1]
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


def normalized(text):
    """Ignore typography and accents when checking editorial concepts."""
    text = unicodedata.normalize("NFKD", text.casefold().replace("’", "'"))
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


@dataclass
class Element:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def text(self):
        return "".join(child.text() if isinstance(child, Element) else child
                       for child in self.children)

    def descendants(self, tag):
        for child in self.children:
            if isinstance(child, Element):
                if child.tag == tag:
                    yield child
                yield from child.descendants(tag)


class PageParser(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        element = Element(tag, dict(attrs))
        self.stack[-1].children.append(element)
        if tag not in VOID_TAGS:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def load_page(path):
    return PageParser((ROOT / path / "index.html").read_text(encoding="utf-8")).root


def visible_faq(page, question_pattern):
    for details in page.descendants("details"):
        summaries = list(details.descendants("summary"))
        if summaries and re.search(question_pattern, normalized(summaries[0].text())):
            answers = list(details.descendants("div"))
            if answers:
                return summaries[0].text(), answers[0].text()
    raise AssertionError("The relevant visible FAQ question and answer must exist")


def structured_faq(page, question_pattern):
    for script in page.descendants("script"):
        if script.attrs.get("type") != "application/ld+json":
            continue
        payload = json.loads(script.text())
        nodes = payload.get("@graph", [payload])
        for node in nodes:
            if node.get("@type") == "FAQPage":
                for question in node.get("mainEntity", []):
                    if re.search(question_pattern, normalized(question["name"])):
                        return question["name"], question["acceptedAnswer"]["text"]
    raise AssertionError("The relevant FAQ question must also exist in JSON-LD")


class MedicalInformationRegressionTests(unittest.TestCase):
    def setUp(self):
        self.infections = load_page("infections-urinaires")
        self.cystoscopy = load_page("cystoscopie-bilan-urodynamique")

    def test_ecbu_paragraphs_and_lists_do_not_require_every_episode(self):
        blocks = [node for tag in ("p", "li")
                  for node in self.infections.descendants(tag)
                  if "ecbu" in normalized(node.text())]
        self.assertTrue(blocks, "Expected ECBU guidance in paragraphs or lists")
        every_episode = r"(?:chaque(?: nouvel)? episode|tous les episodes)"
        negative = r"(?:n'est pas|ne .{0,35} pas|pas necessaire|non systematique)"
        for block in blocks:
            for sentence in re.split(r"[.!?]", normalized(block.text())):
                if re.search(every_episode, sentence):
                    with self.subTest(sentence=sentence):
                        self.assertRegex(
                            sentence, negative,
                            "Do not make ECBU mandatory for every recurrent episode",
                        )

    def test_recurrent_ecbu_guidance_is_qualified_and_preserves_indications(self):
        guidance = [normalized(node.text()) for node in self.infections.descendants("p")
                    if "ecbu" in normalized(node.text())
                    and "recidiv" in normalized(node.text())]
        self.assertTrue(guidance, "Expected an explanation of ECBU in recurrent cystitis")
        text = " ".join(guidance)
        self.assertRegex(text, r"femme")
        self.assertRegex(text, r"(?:cystites? .{0,35} simples?|sans .{0,25}risque .{0,15}complication)")
        self.assertRegex(text, r"premiers? episodes?")
        self.assertRegex(text, r"(?:echec|mauvaise reponse|persistance)")
        self.assertRegex(text, r"(?:medecin|medical)")

    def test_cystoscopy_separates_diagnostic_exam_and_operating_room_procedure(self):
        articles = [article for article in self.cystoscopy.descendants("article")
                    if "treatment-card" in article.attrs.get("class", "").split()
                    and any("cystoscopie" in normalized(h.text())
                            for h in article.descendants("h3"))]
        self.assertEqual(len(articles), 1, "Expected one cystoscopy procedure description")
        heading = " ".join(normalized(h.text()) for h in articles[0].descendants("h3"))
        self.assertIn("diagnostique", heading)
        items = [normalized(item.text()) for item in articles[0].descendants("li")]
        diagnostic = [text for text in items if "anesthesie locale" in text]
        self.assertTrue(any(re.search(r"(?:consultation|soins externes)", text)
                            for text in diagnostic))
        procedures = [text for text in items if re.search(r"(?:biopsie|resection)", text)]
        self.assertTrue(procedures, "Explain the separate biopsy or resection procedure")
        for text in procedures:
            with self.subTest(procedure=text):
                self.assertRegex(text, r"(?:distincte?|separee?)")
                self.assertIn("bloc operatoire", text)
                self.assertIn("generale", text)
                self.assertIn("locoregionale", text)
        preparation = " ".join(items)
        self.assertRegex(preparation, r"consentement.{0,35}specifi")
        self.assertRegex(preparation, r"preparation")
        self.assertRegex(preparation, r"(?:jeune|medicaments)")

    def test_ecbu_faq_preserves_recurrent_cystitis_limits_in_both_formats(self):
        visible = visible_faq(self.infections, r"ecbu")
        structured = structured_faq(self.infections, r"ecbu")
        self.assertEqual(normalized(visible[0]), normalized(structured[0]))
        self.assertEqual(normalized(visible[1]), normalized(structured[1]))
        answer = normalized(visible[1])
        self.assertRegex(answer, r"(?:pas systematique|non systematique)")
        self.assertRegex(answer, r"premiers? episodes?")
        self.assertRegex(answer, r"(?:echec|mauvaise reponse|persistance)")

    def test_fasting_faq_separates_local_exam_and_operating_room_in_both_formats(self):
        visible = visible_faq(self.cystoscopy, r"jeun")
        structured = structured_faq(self.cystoscopy, r"jeun")
        self.assertEqual(normalized(visible[0]), normalized(structured[0]))
        self.assertEqual(normalized(visible[1]), normalized(structured[1]))
        answer = normalized(visible[1])
        self.assertRegex(answer, r"(?:pas|sans).{0,90}anesthesie locale")
        self.assertRegex(answer, r"(?:biopsie|resection).{0,70}bloc operatoire")
        self.assertIn("generale", answer)
        self.assertIn("locoregionale", answer)
        self.assertIn("consignes de jeune", answer)


if __name__ == "__main__":
    unittest.main()

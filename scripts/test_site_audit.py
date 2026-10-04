#!/usr/bin/env python3
import unittest

from site_audit import Parser, external_link_label_errors


class ExternalLinkLabelsTests(unittest.TestCase):
    def parse(self, markup):
        parser = Parser()
        parser.feed(markup)
        parser.close()
        return parser

    def errors(self, markup):
        return external_link_label_errors(self.parse(markup), 'infections-urinaires/index.html')

    def test_original_generic_label_masks_the_visible_label(self):
        self.assertEqual(1, len(self.errors(
            '<a href="https://www.doctolib.fr/chirurgien-urologue/osny/stephane-elard" '
            'target="_blank" rel="noopener noreferrer" '
            'aria-label="Ouvrir ce lien dans un nouvel onglet">Prendre rendez-vous</a>'
        )))

    def test_a_different_generic_label_is_also_rejected(self):
        self.assertEqual(1, len(self.errors(
            '<a href="https://www.facebook.com/" target="_blank" '
            'aria-label="Consulter le site externe">Facebook</a>'
        )))

    def test_distinct_labels_preserve_each_visible_link_name(self):
        self.assertEqual([], self.errors(
            '<a href="https://www.doctolib.fr/" target="_blank" '
            'aria-label="Prendre rendez-vous (nouvel onglet)">Prendre rendez-vous</a>'
            '<a href="https://www.urofrance.org/" target="_blank" '
            'aria-label="Association française d’urologie — Fiche patient : uréthrocystoscopie (nouvel onglet)">'
            'Association française d’urologie — Fiche patient : uréthrocystoscopie</a>'
            '<a href="https://www.linkedin.com/" target="_blank" '
            'aria-label="LinkedIn (nouvel onglet)">LinkedIn</a>'
        ))

    def test_visible_text_is_collected_from_nested_elements_and_entities(self):
        parser = self.parse(
            '<a href="https://www.urofrance.org/" target="_blank" '
            'aria-label="Association française d’urologie — Fiche patient (nouvel onglet)">'
            '<strong>Association française d’urologie</strong>&nbsp;—\n'
            '<span>Fiche patient</span><span hidden>Invisible</span>'
            '<svg aria-hidden="true"><title>Icône</title></svg></a>'
        )
        self.assertEqual('Association française d’urologie\xa0—\nFiche patient', parser.link_texts[0])
        self.assertEqual([], external_link_label_errors(parser, 'vasectomie/index.html'))

    def test_visible_name_is_used_when_aria_label_is_absent(self):
        self.assertEqual([], self.errors(
            '<a href="https://www.linkedin.com/" target="_blank">LinkedIn</a>'
        ))

    def test_empty_explicit_accessible_name_is_rejected(self):
        self.assertEqual(1, len(self.errors(
            '<a href="https://www.linkedin.com/" target="_blank" aria-label="">LinkedIn</a>'
        )))

    def test_existing_internal_and_same_tab_links_are_outside_the_control(self):
        self.assertEqual([], self.errors(
            '<a href="/" target="_blank" aria-label="Retour à l’accueil">Accueil</a>'
            '<a href="https://drelard.com/" target="_blank" aria-label="Retour">Accueil</a>'
            '<a href="https://www.linkedin.com/" aria-label="Partager">LinkedIn</a>'
        ))

    def test_each_link_is_compared_with_its_own_visible_text(self):
        self.assertEqual(2, len(self.errors(
            '<a href="https://www.linkedin.com/" target="_blank" '
            'aria-label="Facebook (nouvel onglet)">LinkedIn</a>'
            '<a href="https://www.facebook.com/" target="_blank" '
            'aria-label="LinkedIn (nouvel onglet)">Facebook</a>'
        )))


if __name__ == '__main__':
    unittest.main()

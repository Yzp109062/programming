import string
import itertools
import random
import time
import codecs
import os
import pickle
from copy import deepcopy

from PhoneticFeatureSpace import PhoneticFeatureSpace
import IPAConverter


DEFAULT_PHONEME_CLASSES = {
    "C": [
        "m", "n", "ɳ", "ɲ", "ŋ",
        "p", "[pʰ]", "b", "t", "[tʰ]", "d", "ʈ", "[ʈʰ]", "ɖ", "c", "[cʰ]", "ɟ", "k", "[kʰ]", "g", "[kʷ]", "[kʷʰ]", "[gʷ]", "q", "[qʰ]", "ɢ", "ʔ", 
        "[pf]", "[pfʰ]", "[bv]", "[tθ]", "[tθʰ]", "[dð]", "[ts]", "[tsʰ]", "[dz]", "[tɬ]", "[tɬʰ]", "[dɮ]", "[tɕ]", "[tɕʰ]", "[dʑ]", "[tʃ]", "[tʃʰ]", "[dʒ]", "[tʂ]", "[tʂʰ]", "[dʐ]", "[cç]", "[cçʰ]", "[ɟʝ]", "[kx]", "[kxʰ]", "[gɣ]", 
        "ɸ", "β", "f", "v", "θ", "ð", "s", "z", "ɬ", "ɮ", "ʃ", "ʒ", "ɕ", "ʑ", "ç", "ʝ", "x", "ɣ", "h", 
        "l", "ɭ", "r", "ɾ", "[ɾʷ]", "ɽ", "j", "w", 
    ],
    "V": ["a", "e", "i", "o", "u", "ʊ", "ɪ", "æ", "ɤ", "ɯ", "ø", "y", "ə", "ɨ", "ɛ", "ɔ", "ɑ", "ɒ", ],
    "I": ["i", "e", ],
    "U": ["u", "o", "a", ],
    "[HV]": ["i", "y", "ɯ", "u", ],
    "Į": ["ʲ", "ˠ", ],
    "F": ["ɸ", "β", "f", "v", "θ", "ð", "s", "z", "ɬ", "ɮ", "ʃ", "ʒ", "ɕ", "ʑ", "ç", "ʝ", "x", "ɣ", "h", ],
    "[AFF]": ["[pf]", "[pfʰ]", "[bv]", "[tθ]", "[tθʰ]", "[dð]", "[ts]", "[tsʰ]", "[dz]", "[tɬ]", "[tɬʰ]", "[dɮ]", "[tɕ]", "[tɕʰ]", "[dʑ]", "[tʃ]", "[tʃʰ]", "[dʒ]", "[tʂ]", "[tʂʰ]", "[dʐ]", "[cç]", "[cçʰ]", "[ɟʝ]", "[kx]", "[kxʰ]", "[gɣ]", ],
    "T": ["t", "[tʰ]", "d", ],
    "N": ["m", "n", "ɳ", "ɲ", "ŋ"],
    "P": ["p", "[pʰ]", "b", "t", "[tʰ]", "d", "ʈ", "[ʈʰ]", "ɖ", "c", "[cʰ]", "ɟ", "k", "[kʰ]", "g", "[kʷ]", "[kʷʰ]", "[gʷ]", "q", "[qʰ]", "ɢ", "ʔ", ],
}


class Language:
    def __init__(self, name, lexicon, phoneme_classes):
        self.name = name
        self.lexicon = lexicon
        self.phoneme_classes = phoneme_classes
        self.used_phonemes = self.get_used_phonemes()

    def get_used_phonemes(self):
        forms = self.lexicon.all_forms()
        res = set()
        for w in forms:
            res |= w.get_phonemes_used()
        return res


class Lexicon:
    def __init__(self, lexemes):
        self.lexemes = lexemes
    
    def add_lexeme(self, lexeme):
        self.lexemes.append(lexeme)

    def all_forms(self):
        res = []
        for lex in self.lexemes:
            res += lex.forms
        return res


class Lexeme:
    def __init__(self, citation_form, forms, part_of_speech, gloss, form_glosses):
        self.citation_form = citation_form
        self.forms = [Word.from_str(w) for w in forms]
        for i, form in enumerate(self.forms):
            assert type(form) is Word
            self.forms[i].designate(self.citation_form.designation + "." + str(i))
        assert part_of_speech.isidentifier(), "part of speech \"{}\" is not a valid identifier".format(part_of_speech)
        self.part_of_speech = part_of_speech
        self.gloss = gloss
        self.form_glosses = form_glosses
        assert len(self.forms) == len(self.form_glosses)
        self.form_to_gloss = {f: g for f, g in zip(self.forms, self.form_glosses)}


class Word:
    def __init__(self, lst, designation=None):
        self.designation = designation
        assert type(lst) is list, "Word.lst must be a list, got {}: {}".format(type(lst), lst)
        self.lst = lst
        #self.word_class = word_class
        
    def designate(self, designation):
        self.designation = designation
        # print("designated {}".format(self))
        
    @staticmethod
    def from_str(s, designation=None):
        lst =  parse_word_str_to_list(s)
        assert type(lst) is list
        return Word(lst, designation)
        
    def to_str(self):
        return "".join(self.lst)
        
    def get_phonemes_used(self):
        return set(self.lst)
        
    def with_word_boundaries(self):
        if self.has_word_boundaries():
            return self
        else:
            lst = ["#"] + self.lst + ["#"]
            return Word(lst, self.designation + "#")
            
    def without_word_boundaries(self):
        if self.has_word_boundaries():
            lst = self.lst[1:-1]
            return Word(lst, self.designation.replace("#",""))
        else:
            return self
            
    def has_word_boundaries(self):
        if "#" in self.lst:
            if self.lst.count("#") == 2 and self.lst[0] == "#" and self.lst[-1] == "#":
                assert "#" in self.designation
                return True
            else:
                raise Exception("word has invalid word boundary positions: {}".format(self))
        else:
            assert "#" not in self.designation
            return False
            
    def __repr__(self):
        # don't put with(out)_word_boundaries() in here because it will call this if it throws an error, causing stack overflow
        return "Word #{} : {}".format(self.designation, "".join(self.lst))
     
    def __len__(self):
        # will count word boundaries if they are present, so be sure to get the length you want by adding or removing boundaries first
        return len(self.lst)
         
    def __getitem__(self, index):
        return self.lst[index]
        
    def __contains__(self, item):
        return item in self.lst
        
    def __eq__(self, other):
        return self.designation == other.designation and self.to_str() == other.to_str()

    def __hash__(self):
        return hash((self.designation, self.to_str()))
        
        
class Rule:
    def __init__(self, inp, outp, designation=None):
        self.designation = designation
        self.input = inp
        self.output = outp
    
    @staticmethod
    def from_str(s):
        rules = parse_rule_str(s)
        # don't designate unless it will be used, so put the designate() call elsewhere
        return rules
        
    def to_str(self):
        return self.get_input_str() + " -> " + self.get_output_str()

    def to_notation(self):
        return self.get_input_str() + ">" + self.get_output_str()
        
    def designate(self, s):
        assert type(s) is str, "designation must be str, got {}".format(type(s))
        self.designation = s
        # print("designated {}".format(self))
        
    def get_specific_cases(self, classes, used_phonemes):
        inp = self.input
        outp = self.output
        n = len(inp)
        assert n == len(outp), "rule with unequal lengths: {}".format(self)
        for i in range(n):
            if inp[i] in classes:
                assert outp[i] == inp[i] or outp[i] not in classes
                replace = outp[i] != inp[i]
                res = []
                vals = [x for x in classes[inp[i]] if x in used_phonemes]
                for val_i, val in enumerate(vals):
                    replacement = outp[i] if replace else val
                    new_inp = inp[:i] + [val] + inp[i+1:]
                    new_outp = outp[:i] + [replacement] + outp[i+1:]
                    designation = "{}.{}".format(self.designation, val_i)
                    new_rule = Rule(new_inp, new_outp)
                    new_rule.designate(designation)
                    res += new_rule.get_specific_cases(classes, used_phonemes)
                return res
        else:
            return [self] if inp != outp else []
            
    @staticmethod
    def expand_classes(s, classes, used_phonemes):
        n = len(s)
        for i in range(n):
            if s[i] in classes:
                #replace = outp[i] != inp[i]
                res = []
                vals = [x for x in classes[s[i]] if x in used_phonemes]
                for val in vals:
                    new_s = s[:i] + [val] + s[i+1:]
                    res += Rule.expand_classes(new_s, classes, used_phonemes)
                return res
        else:
            return [s]
            
    def get_output_phonemes_used(self):
        if self.has_classes():
            raise Exception("can only get output phonemes from specific case, but this rule is a general case: {}".format(self))
        return set(self.output)
        
    def get_input_str(self):
        return "".join(("_" if x == "" else x) for x in self.input)
        
    def get_output_str(self):
        s = "".join(self.output)
        return "Ø" if s == "" else s
        
    def has_classes(self):
        return any(x in string.ascii_uppercase for x in self.to_str())
        
    def get_input_no_blanks(self):
        return [x for x in self.input if x != ""]
    
    def __repr__(self):
        rule_str = self.to_str()
        return "Rule #{} : {}".format(self.designation, rule_str)


class Phone:
    def __init__(self, features_dict):
        assert all(type(v) is int for v in features_dict.values())
        self.features = features_dict

    def print(self, verbose=False):
        print(self.str(verbose=verbose))

    def str(self, verbose=False):
        if verbose:
            s = ""
            d = self.features
            get_name = lambda k, v: PhoneticFeatureSpace.FEATURE_KEYS[k][v]
            for k, val in d.items():
                if type(val) is int:
                    translated_val = get_name(k, val)
                else:
                    raise TypeError("feature dict values were not list or int, but {}".format(type(val)))
                s += "{}: {}\n".format(k, translated_val)
            return s
        else:
            return self.get_ipa_symbol()

    def get_ipa_symbol(self):
        return Phone.get_ipa_symbol_from_features(self.features)

    @staticmethod
    def from_ipa_symbol(symbol):
        if symbol == "#":
            return WordBoundaryPhone()
        else:
            return Phone(IPAConverter.get_features_from_symbol(symbol))

    @staticmethod
    def get_ipa_symbol_from_features(features):
        if type(features) is not dict:
            raise TypeError("features must be dict if using this method; if possible, use get_ipa_symbol method of Phone object")

        if features.get("is_word_boundary") == 1:
            return "#"

        phone = Phone(features)

        phone = phone.restrict_features()

        if phone.features["syllabicity"] == 0:
            return Phone.get_ipa_consonant_symbol_from_features(phone.features)

        if phone.features["syllabicity"] == 1:
            return Phone.get_ipa_vowel_symbol_from_features(phone.features) + "\u032f"

        if phone.features["syllabicity"] == 2:
            return Phone.get_ipa_consonant_symbol_from_features(phone.features) + "\u0329"

        elif phone.features["syllabicity"] == 3:
            return Phone.get_ipa_vowel_symbol_from_features(phone.features)

        else:
            raise ValueError("invalid syllabicity of {} for features_dict\n{}".format(phone.features["syllabicity"], features))

    @staticmethod
    def get_ipa_consonant_symbol_from_features(features, with_secondaries=True):
        # code = Phone.get_numerical_code_from_features(features)
        code = "_"
        secondaries = Phone.get_secondary_symbols_from_features(features) if with_secondaries else ""

        if features["c_manner"] == 0 and features["nasalization"] == 1:
            symbol = ["m", "\u0271", "n\u032a", "n", "n\u0320", "\u0273", "\u0272", "\u014b", "\u0274", code, code, code][features["c_place"]]
            if features["voicing"] == 0:
                symbol += ["\u0325", "\u030a", "\u0325", "\u0325", "\u0325", "\u030a", "\u030a", "\u030a", "\u0325", code, code, code][features["c_place"]]
            return symbol + secondaries

        if features["c_manner"] == 0:
            if features["voicing"] == 0:
                symbol = ["p", "p\u032a", "t\u032a", "t", "t\u0320", "\u0288", "c", "k", "q", code, "\u02a1", "\u0294"][features["c_place"]]
            elif features["voicing"] == 1:
                symbol = ["b", "b\u032a", "d\u032a", "d", "d\u0320", "\u0256", "\u025f", "g", "\u0262", code, code, code][features["c_place"]]
            return symbol + secondaries

        if features["c_manner"] == 1:
            plosive_features = deepcopy(features)
            plosive_features["c_manner"] = 0
            plosive_symbol = Phone.get_ipa_consonant_symbol_from_features(plosive_features, with_secondaries=False)

            fricative_features = deepcopy(features)
            fricative_features["c_manner"] = 2
            fricative_symbol = Phone.get_ipa_consonant_symbol_from_features(fricative_features, with_secondaries=False)

            tie_bar_above = True
            tie_symbol = "\u0361" if tie_bar_above else "\u035c"
            symbol = plosive_symbol + tie_symbol + fricative_symbol

            return symbol + secondaries

        if features["c_manner"] == 2:
            if features["voicing"] == 0:
                symbol = ["\u0278", "f", "\u03b8", "s", "\u0283", "\u0282", "\u00e7", "x", "\u03c7", "\u0127", "\u029c", "h"][features["c_place"]]
            elif features["voicing"] == 1:
                symbol = ["\u03b2", "v", "\u00f0", "z", "\u0292", "\u0290", "\u029d", "\u0263", "\u0281", "\u0295", "\u02a2", "\u0266"][features["c_place"]]
            return symbol + secondaries

        if features["c_manner"] == 3:
            if features["c_labialization"] == 1 and features["c_place"] in [6, 7]:
                symbol = [None, None, None, None, None, None, "\u0265", "w", None, None, None, None][features["c_place"]]
            else:
                symbol = ["\u03b2\u031e", "\u028b", "\u0279\u032a", "\u0279", "\u0279\u0320", "\u027b", "j", "\u0270", code, code, code, code][features["c_place"]]
            if features["voicing"] == 0:
                symbol += ["\u0325", "\u0325", "\u0325", "\u0325", "\u0325", "\u030a", "\u030a", "\u030a", "", "", "", ""][features["c_place"]]
            return symbol + secondaries

        return code

    @staticmethod
    def get_ipa_vowel_symbol_from_features(features, with_secondaries=True):
        # code = Phone.get_numerical_code_from_features(features)
        code = "_"
        secondaries = Phone.get_secondary_symbols_from_features(features) if with_secondaries else ""

        if features["v_height"] == 0:
            if features["v_roundedness"] == 0:
                symbol = ["a", "a\u0308", "\u0251"][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = ["\u0276", "\u0276\u0308", "\u0252"][features["v_backness"]]
            return symbol + secondaries

        if features["v_height"] == 1:
            if features["v_roundedness"] == 0:
                symbol = ["\u00e6", "\u0250", code][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = [code, code, code][features["v_backness"]]
            return symbol + secondaries

        if features["v_height"] == 2:
            if features["v_roundedness"] == 0:
                symbol = ["\u025b", "\u025c", "\u028c"][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = ["\u0153", "\u025e", "\u0254"][features["v_backness"]]
            return symbol + secondaries

        if features["v_height"] == 3:
            if features["v_roundedness"] == 0:
                symbol = ["e\u031e", "\u0259", "\u0264\u031e"][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = ["\u00f8\u031e", "\u0275\u031e", "o\u031e"][features["v_backness"]]
            return symbol + secondaries

        if features["v_height"] == 4:
            if features["v_roundedness"] == 0:
                symbol = ["e", "\u0258", "\u0264"][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = ["\u00f8", "\u0275", "o"][features["v_backness"]]
            return symbol + secondaries

        if features["v_height"] == 5:
            if features["v_roundedness"] == 0:
                symbol = ["\u026a", code, "\u026a\u0320"][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = ["\u028f", code, "\u028a"][features["v_backness"]]
            return symbol + secondaries

        if features["v_height"] == 6:
            if features["v_roundedness"] == 0:
                symbol = ["i", "\u0268", "\u026f"][features["v_backness"]]
            elif features["v_roundedness"] == 1:
                symbol = ["y", "\u0289", "u"][features["v_backness"]]
            return symbol + secondaries

        return code

    @staticmethod
    def get_secondary_symbols_from_features(features):
        result = ""

        if features["nasalization"] == 1:
            if features["c_manner"] != 0:
                result += "\u0303"

        if features["c_palatization"] == 1:
            result += "\u02b2"

        if features["c_labialization"] == 1:
            if features["c_manner"] != 3 and features["c_place"] not in [6, 7]:
                result += "\u02b7"

        if features["c_velarization"] == 1:
            result += "\u02e0"

        if features["c_pharyngealization"] == 1:
            result += "\u02e4"

        if features["c_glottalization"] == 1:
            if features["syllabicity"] in [1, 3] or features["voicing"] == 1:
                result += "\u0330"
            else:
                result += "\u02bc"

        if features["c_aspiration"] == 1:
            if features["voicing"] == 0:
                result += "\u02b0"
            else:
                result += "\u02b1"

        if features["length"] == 1:
            result += "\u02d0"

        return result

    @staticmethod
    def get_numerical_code_from_features(features):
        # return "_"
        # return repr(features)
        return "\n\n<?" + ",".join([str(v) for k, v in sorted(features.items())]) + ">\n\n"

    @staticmethod
    def get_random_features():
        d = {}
        for k, v in PhoneticFeatureSpace.FEATURE_KEYS.items():
            d[k] = random.choice([x for x in v.keys()])
        return d

    def restrict_features(self):
        features = deepcopy(self.features)

        # no nasalization while voiceless
        if features["nasalization"] == 1 and features["voicing"] == 0:
            features["nasalization"] = 0

        # uvular/pharyngeal/epiglottal approximant -> fricative
        if features["c_place"] in [8, 9, 10] and features["c_manner"] == 3:
            features["c_manner"] = 2

        # glottal approximant -> fricative
        if features["c_place"] == 11 and features["c_manner"] == 3:
            features["c_manner"] = 2

        # pharyngeal stop -> epiglottal
        if features["c_place"] == 9 and features["c_manner"] == 0:
            features["c_place"] = 10

        # voiced epiglottal/glottal stop/affricate -> voiceless
        if features["c_place"] in [10, 11] and features["c_manner"] in [0, 1] and features["voicing"] == 1:
            features["voicing"] = 0

        # labialized bilabial/labiodental -> non-labialized
        if features["c_place"] in [0, 1] and features["c_labialization"] == 1:
            features["c_labialization"] = 0

        # pharyngealized/glottalized pharyngeal/epiglottal/glottal -> non-*
        if features["c_place"] in [9, 10, 11]:
            features["c_pharyngealization"] = 0
            features["c_glottalization"] = 0

        # palatized palatal -> non-palatized
        if features["c_place"] == 6 and features["c_palatization"] == 1:
            features["c_palatization"] = 0

        # velarized velar+ -> non-velarized
        if features["c_place"] in [7, 8, 9, 10, 11] and features["c_velarization"] == 1:
            features["c_velarization"] = 0

        # aspirated h -> non-aspirated
        if features["c_place"] in [9, 10, 11] and features["c_manner"] == 2 and features["c_aspiration"] == 1:
            features["c_aspiration"] = 0

        # velarized vowels -> back
        if features["syllabicity"] in [1, 3] and features["c_velarization"] == 1:
            features["v_backness"] = 2
            features["c_velarization"] = 0

        # palatized vowels -> front
        if features["syllabicity"] in [1, 3] and features["c_palatization"] == 1:
            features["v_backness"] = 0
            features["c_palatization"] = 0

        # labialized vowels -> rounded
        if features["syllabicity"] in [1, 3] and features["c_labialization"] == 1:
            features["v_roundedness"] = 1
            features["c_labialization"] = 0

        # aspirated/pharyngealized vowel -> non-*
        if features["syllabicity"] in [1, 3]:
            features["c_aspiration"] = 0
            features["c_pharyngealization"] = 0

        # aspirated and glottalized -> glottalized
        if features["c_glottalization"] == 1 and features["c_aspiration"] == 1:
            features["c_aspiration"] = 0

        # syllabic consonants must not contain plosive
        if features["syllabicity"] == 2 and features["c_manner"] in [0, 1]:
            features["syllabicity"] = 0

        # high semivowels -> consonants, excluding central
        if features["syllabicity"] == 1 and features["v_height"] == 6 and features["v_backness"] in [0, 2]:
            features["syllabicity"] = 0
            features["c_labialization"] = features["v_roundedness"]
            if features["v_backness"] == 0:
                features["c_place"] = 6
            elif features["v_backness"] == 2:
                features["c_place"] = 7

        # aspirated approximant -> non-aspirated
        if features["c_manner"] == 3:
            features["c_aspiration"] = 0

        return Phone(features)


class WordBoundaryPhone(Phone):
    def __init__(self):
        self.features = {"is_word_boundary": 1}

    def __eq__(self, other):
        return type(other) is WordBoundaryPhone and self.features["is_word_boundary"] == other.features["is_word_boundary"] == 1

    def restrict_features(self):
        return WordBoundaryPhone()


class Phoneme:
    def __init__(self):
        raise
        self.primary_phone = []
        self.allophones = []


class Phonology:
    def __init__(self, inventory, syllable_structure_set):
        self.inventory = inventory
        self.syllable_structure_set = syllable_structure_set


class PhoneticEnvironment:
    def __init__(self, before_environment, after_environment):
        self.before_environment = before_environment
        self.after_environment = after_environment
        # should be able to match underspecified feature dicts


class SoundChange:
    COMMON_SOUND_CHANGES = [
        ({"voicing": 0}, {"voicing": 1}, [{"syllabicity": 3}], [{"syllabicity": 3}]),  # intervocalic voicing
        ({"syllabicity": 3}, {"v_backness": 2}, [{"syllabicity": [0, 2], "c_place": [8, 9, 10, 11]}], []),  # vowels move back after uvulars+
    ]

    def __init__(self, from_features, to_features, phonetic_environment):
        self.from_features = from_features
        self.to_features = to_features
        self.phonetic_environment = phonetic_environment

    def apply_to_word(self, word):
        if self.from_features == "" and self.to_features == "":
            raise Exception("bad practice! features should be feature dicts, and if they do nothing, then make them dicts that somehow say that")  # FIXME
            return word

        phoneme_list = [WordBoundaryPhone()] + word.get_phoneme_list() + [WordBoundaryPhone()]

        before_features_list = self.phonetic_environment.before_environment
        after_features_list = self.phonetic_environment.after_environment
        before_len = len(before_features_list)
        start_index = before_len
        after_len = len(after_features_list)
        end_index_exclusive = len(phoneme_list) - after_len

        new_phoneme_list = []

        if type(self.from_features) is dict:
            for i, phone in enumerate(phoneme_list):
                if i < before_len or i >= end_index_exclusive:
                    new_phoneme_list.append(deepcopy(phone))
                    continue

                before_environment = phoneme_list[i - before_len: i]
                after_environment = phoneme_list[i + 1: i + after_len + 1]

                matches_phone = matches_features_dict(phone, self.from_features)
                if not matches_phone:
                    new_phoneme_list.append(deepcopy(phone))
                    continue

                matches_before = all([matches_features_dict(before_environment[j], before_features_list[j]) for j in range(before_len)])
                matches_after = all([matches_features_dict(after_environment[j], after_features_list[j]) for j in range(after_len)])
                if matches_before and matches_after:
                    if self.to_features == "":
                        new_phoneme_list.append(None)
                    else:
                        new_phone = deepcopy(phone)
                        new_phone.update(self.to_features)
                        new_phoneme_list.append(new_phone)
                else:
                    new_phoneme_list.append(deepcopy(phone))

        elif self.from_features == "":
            for i, phone in enumerate(phoneme_list):
                if i < before_len or i >= end_index_exclusive:
                    new_phoneme_list.append(deepcopy(phone))
                    continue

                before_environment = phoneme_list[i - before_len: i]
                after_environment = phoneme_list[i: i + after_len]

                matches_before = all([matches_features_dict(before_environment[j], before_features_list[j]) for j in range(before_len)])
                matches_after = all([matches_features_dict(after_environment[j], after_features_list[j]) for j in range(after_len)])
                if matches_before and matches_after:
                    new_phone = DEFAULT_FEATURE_VALUES
                    new_phone.update(self.to_features)
                    new_phoneme_list.append(new_phone)
                    new_phoneme_list.append(deepcopy(phone))
                else:
                    new_phoneme_list.append(deepcopy(phone))

        else:
            raise ValueError("invalid self.from_features: {0}".format(self.from_features))

        return LE2Word.from_phone_list([x for x in new_phoneme_list if x is not None])

    @staticmethod
    def get_random_sound_change_from_inventory(inventory):
        feature, value = get_random_feature_value_from_inventory(inventory)
        feature2, value2 = get_random_feature_value_from_inventory(inventory)
        feature3, value3 = get_random_feature_value_from_inventory(inventory)
        feature4, value4 = get_random_feature_value_from_inventory(inventory)
    
        from_features = {feature: value} if random.random() < 0.95 else ""
        to_features = {feature2: random.choice([i for i in PhoneticFeatureSpace.FEATURE_KEYS[feature2].keys()])} if random.random() < 0.95 else ""
        before_environment = {feature3: value3} if random.random() < 0.8 else WordBoundaryPhone().features
        after_environment = {feature4: value4} if random.random() < 0.8 else WordBoundaryPhone().features

        phonetic_environment = PhoneticEnvironment([before_environment], [after_environment])
        return SoundChange(from_features, to_features, phonetic_environment)


class Syllable:
    def __init__(self, phonemes):
        self.phonemes = phonemes


class LE2Word:
    def __init__(self, syllables):
        assert type(syllables) is list and all(type(x) is Syllable for x in syllables), "invalid syllables passed to Word: {}".format(syllables)
        self.syllables = syllables

    def __add__(self, other):
        if type(other) is LE2Word:
            return LE2Word(self.syllables + other.syllables)  # TODO: re-syllabify if necessary
        else:
            return NotImplemented

    def get_phoneme_list(self):
        lst = []
        for syll in self.syllables:
            lst.extend(syll.phonemes)
        return lst

    def get_ipa_str(self):
        phoneme_list = self.get_phoneme_list()
        return "".join(phone.get_ipa_symbol() for phone in phoneme_list)

    @staticmethod
    def from_user_input():
        print("Input a word to add to the language.\nFormat: phonemes separated by spaces, syllables separated by hyphens or dollar signs")
        print("Example: k a - t i")
        inp = input("word: ")
        inp = inp.replace("$", "-").strip()
        if inp == "":
            return []
        syllables = inp.split("-")
        syllables = [syll.strip().split() for syll in syllables]
        syllables = [Syllable(phones_lst) for phones_lst in syllables]
        return LE2Word(syllables)

    @staticmethod
    def from_string(s):
        word = []
        for symbol in s:
            if symbol not in ["-", "\ufeff"]:
                phone = Phone.from_ipa_symbol(symbol)
                word.append(phone)
        return word

    @staticmethod
    def from_phone_list(lst):
        # TODO: add ability to syllabify the list given a Phonology object
        syllables = [Syllable(lst)]
        return LE2Word(syllables)

    @staticmethod
    def get_random_phone_sequence(n_syllables, inventory, syllable_structure):
        syllables = []
        for i in range(n_syllables):
            syllable_phonemes = []
            for typ in syllable_structure:
                if typ == "C":
                    cands = [x for x in inventory.phonemes if x.features["syllabicity"] in [0, 1]]
                    chosen = random.choice(cands) if cands != [] else None
                elif typ == "V":
                    cands = [x for x in inventory.phonemes if x.features["syllabicity"] in [2, 3]]
                    chosen = random.choice(cands) if cands != [] else None
                elif typ == "N":
                    cands = [x for x in inventory.phonemes if x.features["syllabicity"] == 0 and x.features["nasalization"] == 1 and x.features["c_manner"] == 0]
                    chosen = random.choice(cands) if cands != [] else None
                else:
                    chosen = random.choice(inventory.phonemes)
    
                if chosen is not None:
                    syllable_phonemes.append(chosen)
            syllables.append(Syllable(syllable_phonemes))
        return LE2Word(syllables)

    def print(self, as_word=False, verbose=False):
        if verbose:
            for d in lst:
                phone = Phone(d)
                print("symbol: {}".format(phone.get_ipa_symbol()))
                phone.print()
                input()
        else:
            s = ""
            for syll in self.syllables:
                for phone in syll.phonemes:
                    s += phone.get_ipa_symbol()
            print(s)
            # delim = ""
            # print(delim.join(Phone.get_ipa_symbol_from_features(d) for d in lst))
        print()




class LE2Lexicon:
    def __init__(self, words):
        self.words = words

    @staticmethod
    def from_user_input():
        print("Add words. When finished, press enter without entering anything.")
        words = []
        while True:
            w = LE2Word.from_user_input()
            if w == []:
                break
            words.append(w)
        return LE2Lexicon(words)

    @staticmethod
    def from_phonology(phonology):
        vocabulary = []
        for i in range(3):
            paradigm = get_random_paradigm(phonology.inventory, phonology.syllable_structure_set)
            for word in paradigm:
                vocabulary.append(word)
        return vocabulary



class Inventory:
    def __init__(self, phonemes):
        self.phonemes = phonemes

    @staticmethod
    def random():
        feature_space = PhoneticFeatureSpace.get_random_feature_value_sets()
        print("phonetic feature space:")
        feature_space.print()
        input()
        raw_inventory = Inventory([Phone(feature_space.get_features_from_possible_values()) for i in range(40)])
        print("raw inventory ({} phonemes):".format(len(raw_inventory.phonemes)))
        raw_inventory.print()
        input()
        seen = []
        seen_symbols = []
        for phone in raw_inventory.phonemes:
            restricted_phone = phone.restrict_features()
            symbol = restricted_phone.get_ipa_symbol()
            print("new symbol: {}\nexisting symbols: {}".format(symbol, seen_symbols))
            if symbol not in seen_symbols and "_" not in symbol and "?" not in symbol:
                seen.append(restricted_phone)
                seen_symbols.append(symbol)
        inventory = Inventory(seen)
        print("final inventory:")
        inventory.print()
        input()
        return inventory


    @staticmethod
    def from_lexicon(lexicon):
        added_phoneme_symbols = set()
        for word in lexicon.words:
            for syll in word.syllables:
                for symbol in syll.phonemes:
                    added_phoneme_symbols.add(symbol)

        phonemes = []
        for symbol in added_phoneme_symbols:
            try:
                phoneme = Phone.from_ipa_symbol(symbol)

            except KeyError:
                features_dict = {}
                print("the phoneme {} was not found in the IPA symbols. Please specify what it is:".format(symbol))
                for k, d in PhoneticFeatureSpace.FEATURE_KEYS.items():
                    print("{}: {}".format(k, d))
                    while True:
                        inp = input("choice for this feature: ")
                        try: 
                            choice = int(inp.strip())
                            if choice not in d:
                                print("that choice is not valid, must be one of {}".format(sorted(d.keys())))
                                continue
                            features_dict[k] = choice
                            break
                        except ValueError:
                            print("invalid int")
                            continue
                phoneme = Phone(features_dict)

            phonemes.append(phoneme)

        inventory = Inventory(phonemes)
        print("resulting inventory:")
        inventory.print()
        input()

        return inventory

    def print(self):
        print(self.str())
        print()

    def str(self):
        delim = " , "
        return delim.join(phone.str() for phone in self.phonemes)


class LE2Language:
    def __init__(self, inventory, **args):
        self.inventory = inventory


def evolve_word(word, rules):
    for rule in rules:
        word = apply_rule(word, rule)
    return word

def parse_word_str_to_list(w):
    lst = []
    inside_brackets = False
    current_item = ""
    for c in w:
        if inside_brackets:
            assert c != "["
            # no nesting allowed, no meta-digraphs
            if c == "]":
                current_item += c
                lst.append(current_item)
                current_item = ""
                inside_brackets = False
            else:
                current_item += c
        else:
            if c == "[":
                assert current_item == ""
                current_item += c
                inside_brackets = True
            elif c == "_":
                # use this to make blanks in rules with string notation
                lst.append("")
            else:
                lst.append(c)
    return lst

def parse_rule_str(inp):
    rule_strs = inp.split(",")
    all_results = []
    for rule_str in rule_strs:
        if rule_str.count(">") != 1:
            print("skipping invalid rule_str:", rule_str)
            continue
        rule_inp_str, rule_outp_str = rule_str.split(">")
        if rule_inp_str.count("_") > 1:
            print("only insertions with one blank are accepted right now; please split this into a series of rules:", rule_str)
            continue
        if len(rule_inp_str) != len(rule_outp_str):
            lris = len(rule_inp_str)
            lros = len(rule_outp_str)
            input_shorter = lris < lros
            shorter_one, shorter_len, longer_len = (rule_inp_str, lris, lros) if input_shorter else (rule_outp_str, lros, lris)
            shorter_one += "_" * (longer_len - shorter_len)
            if input_shorter:
                rule_inp_str = shorter_one
            else:
                rule_outp_str = shorter_one
        rule_inp = parse_word_str_to_list(rule_inp_str)
        rule_outp = parse_word_str_to_list(rule_outp_str)
        if len(rule_inp) != len(rule_outp):
            raise AssertionError("invalid rule given, unequal input and output lengths\ninput: {}\noutput: {}".format(rule_inp, rule_outp))
        new_rule = Rule(rule_inp, rule_outp)
        #all_results += new_rule.get_specific_cases(classes, used_phonemes)  # do expansion later
        all_results.append(new_rule)
        
    return all_results
            
def rule_applies(word, rule):
    word = word.with_word_boundaries()
    inp_no_blanks = rule.get_input_no_blanks()
    return list_contains(word, inp_no_blanks)

def get_inputs_that_could_apply(word):
    # ignoring blanks, so check (classless) rules for inclusion in the list that is returned by this function, based on presence of their input without blanks
    # returns triangle number of sublists of word
    if type(word) is str:
        word = parse_word_str_to_list(word)
        
    word = word.with_word_boundaries()
    res = []
    for length in range(1, len(word) + 1):
        n_lists = len(word) - length + 1
        for i in range(n_lists):
            res.append(word[i:i+length])
    return res
    
def apply_rule(word, rule):
    try:
        assert "#" not in word
        inp = rule.input
        outp = rule.output
        assert inp.count("#") == outp.count("#") <= 2, "too many '#'s in rule {}".format(rule)
    except AssertionError:
        print("invalid word for rule application:", word)
        return word
    
    word2 = word.with_word_boundaries()
    res_lst = sublist_replace(word2.lst,inp, outp)
    res_lst = [x for x in res_lst if x not in ["#", ""]]
    if res_lst == []:
        print("Warning: blocking change {} that would make {} into a blank word".format(rule, word))
        return word
    
    if res_lst != word.lst:
        res = Word(res_lst, designation=word.designation)
        #outp_display = "Ø" if outp == "" else "".join(outp)
        #print("{} : {} -> {}".format(rule, word, res))
        return res
    else:
        return word
    
def sublist_replace(lst, old, new):
    assert len(old) == len(new)  # true for this use case
    insert = "" in old
    if insert:
        assert old.count("") == 1
    b = old.index("") if insert else None
    n = len([x for x in old if x != ""])
    m = len([x for x in new if x != ""])
    #print("\n{}, {} -> {}".format(lst, old, new))
    #print("n {}, m {}".format(n, m))
    new_no_blanks = [x for x in new if x != ""]
    word_len = len(lst)
    index_offset = 0
    for i in range(word_len - n + 1):
        j = i + index_offset
        #print(i, index_offset, j)
        slice = lst[j:j+n]
        #print("slice", slice)
        if insert:
            new_slice = []
            for k in range(n+1):
                if k < b:
                    new_slice.append(slice[k])
                elif k == b:
                    new_slice.append("")
                else:
                    new_slice.append(slice[k-1])
            slice = new_slice
            #print("insert, slice now =", slice)
        if slice == old:
            lst = lst[:j] + new_no_blanks + lst[j+n:]
            #print("lst now", lst)
            #input("please review")
            index_offset += m-n
    return lst
   
def get_random_rules(n_rules, lexicon, classes):
    res = []
    for _ in range(n_rules):
        w = random.choice(lexicon)
        w = w.with_word_boundaries()
        n = len(w)
        max_env_len = min(4, n-1)
        env_len = random.randint(1, max_env_len)
        max_start_index = n - env_len
        min_start_index = 0
        typ = random.choice(
            ["insertion"] * 1 +\
            ["deletion"] * 3 +\
            ["mutation"] * 6
        )
        if env_len == 1 and typ != "insertion":
            # only do insertions if the whole environment is a word boundary
            min_start_index += 1
            max_start_index -= 1
        assert min_start_index <= max_start_index, "non-overlapping indices with parameters\nword = {w}\ntyp = {typ}\nenv_len = {env_len}\nindices = {min_start_index}, {max_start_index}".format(**locals())
        start_index = random.randint(min_start_index, max_start_index)
        end_index = start_index + env_len
        inp = list(w[start_index : end_index])
        if typ == "insertion":
            # add a blank somewhere
            if inp[0] == "#":
                min_blank_index = 1
            else:
                min_blank_index = 0
            if inp[-1] == "#":
                max_blank_index = len(inp) - 1
            else:
                max_blank_index = len(inp)
            if min_blank_index == 1 and max_blank_index == 0:
                # insertion where input is just ["#"], pick beginning or end of word
                blank_index = random.choice([0, 1])
            else:
                blank_index = random.randint(min_blank_index, max_blank_index)
            inp = inp[:blank_index] + [""] + inp[blank_index:]
            change_index = blank_index
        else:
            while True:
                change_index = random.randrange(len(inp))
                if inp[change_index] != "#":
                    break
        
        # put some classes in inp, with some probability
        # echo these classes in outp, all changes are to nothing or a specific string with no classes
        # e.g., can't make rule like [["#", "", "a"], ["#", "C", "a"]] because don't know which C to insert!
                
        for i, seg in enumerate(inp):
            if len(inp) > 1 and random.random() < 0.3:
                # don't have changes like C -> s or V -> Ø
                classes_with_seg = [c for c in classes if seg in classes[c]]
                if len(classes_with_seg) == 0:
                    continue
                
                c = random.choice(classes_with_seg)
                inp[i] = c
            
        # now copy input as output and do something to it
        outp = inp[:]
        if typ == "insertion":
            c = random.choice(list(classes.keys()))  # make this better later, e.g. don't do C_C -> CfC
            outp[change_index] = random.choice(classes[c])
        elif typ == "deletion":
            outp[change_index] = ""
        elif typ == "mutation":
            if inp[change_index] in classes:
                possibilities = classes[inp[change_index]]
                outp[change_index] = random.choice(possibilities)
            else:
                classes_with_seg = [c for c in classes if inp[change_index] in classes[c]]
                if len(classes_with_seg) == 0:
                    raise Exception("segment to be changed ({}) is not in any class".format(inp[change_index]))
                
                c = random.choice(classes_with_seg)
                outp[change_index] = random.choice([x for x in classes[c] if x != inp[change_index]])
        else:
            raise Exception("unknown change type")
        
        rule = Rule(inp, outp)  # don't designate it until it is accepted for use
        print("generated rule: {}".format(rule))
        res.append(rule)
    
    return res

def to_cv(word, classes):
    res = []
    cs = classes["C"]
    vs = classes["V"]
    assert set(cs) & set(vs) == set()
    for c in word:
        res.append("C" if c in cs else "V" if c in vs else "*")
    return res

def list_contains(lst, sub):
    for i in range(len(lst) - len(sub) + 1):
        if lst[i:i+len(sub)] == sub:
            return True
    return False

def cleanup(word, classes, okay_seqs, new_rules, used_phonemes):
    dirty = False
    original_word = word
    for seq in okay_seqs:
        if list_contains(word, seq):
            #print("okayed sequence:", seq)
            word = sublist_replace(word, seq, ["*"] * len(seq))
            
    for r in new_rules:
        # assert type(word) is list
        if rule_applies(word, r):
            #print("new rule will be applied:", r)
            pass
        
    cv = to_cv(word, classes)
    
    if any(list_contains(word, [x]*3) for c in classes.values() for x in c):
        print("\nword has triple sound")
        dirty = True
        
    if all(x not in word for x in classes["V"]):
        print("\nword has no vowels")
        dirty = True
        
    if any(list_contains(word, [x, y, z]) for x in classes["V"] for y in classes["[HV]"] for z in classes["V"]):
        print("\nword has intervocalic high vowel")
        dirty = True
        
    if list_contains(cv, ["V"]*3):
        print("\nword has 3 vowels in a row")
        dirty = True
        
    if dirty:
        #print(original_word)
        word, user_okay_seqs, user_new_rules = user_edit(original_word, classes, used_phonemes)
        user_okay_seqs_expanded = []
        for seq in user_okay_seqs:
            user_okay_seqs_expanded += Rule.expand_classes(seq, classes, used_phonemes)
        print("got okay seqs", user_okay_seqs_expanded)
        print("got new rules", user_new_rules)
        okay_seqs += user_okay_seqs_expanded
        new_rules += user_new_rules
    else:
        word = original_word
    return word, okay_seqs, new_rules
    
def user_edit(word, classes, used_phonemes):
    #print("list form:", word)
    #print("word as string:", "".join(word))
    print("editing", word)
    print("input edited word in string form, e.g. *iai or *iai,aai to okay sequence(s), e.g. ViV>VjV,m_a>mba to make rules, or nothing to keep as is")
    okay_seqs = []
    new_rules = []
    while True:
        inp = input("input:\n")
        if inp == "":
            return word, okay_seqs, new_rules
        elif inp[0] == "*":
            okay_seqs += [parse_word_str_to_list(x) for x in inp[1:].split(",")]
        elif ">" in inp:
            try:
                rules_from_inp = parse_rule_str(inp)
                new_rules += rules_from_inp
            except AssertionError:
                print("invalid rule input")
        else:
            inp_word = Word.from_str(inp)
            print("resulting word:", inp_word)
            if input("is this correct? (default yes, n for no)") != "n":
                print()
                inp_word.designate(word.designation)
                return inp_word, okay_seqs, new_rules

def evolve_user_input_words(rules1, rules2, lexicon):
    new_proto_words = []
    next_designation = 1 + max(int(x.designation) for x in lexicon)
    while True:
        inp = input("\nenter a word to evolve, or nothing to exit\n")
        if inp == "":
            break
        if ">" in inp or "," in inp or "*" in inp:
            # prevent crashing just because I misread the prompt
            print("oops! looks like you didn't give a valid word")
            continue
        inp = Word.from_str(inp)
        inp.designate("None")
        e1 = evolve_word(inp, rules1)
        e2 = evolve_word(inp, rules2)
        print("\nresulting evolutions:\n1. {}\n2. {}\n".format(e1, e2))
        if input("add this proto-word to the lexicon? (y/n, default yes)") != "n":
            inp.designate(str(next_designation))
            next_designation += 1
            # lexicon.append(inp) # put it in original_words instead
            new_proto_words.append(inp)
    return new_proto_words

def create_rules_from_rule_strs(rule_strs, next_rule_designation=0):
    rules = []
    next_rule_designation = 0
    for s in rule_strs:
        rules_from_str = Rule.from_str(s)
        for r in rules_from_str:
            r.designate(str(next_rule_designation))
            next_rule_designation += 1
            rules.append(r)
    return rules, next_rule_designation
    
def build_lexicon_strs(classes):
    assert "C" in classes and "V" in classes
    word_strs = []
    # desig = 0
    used_phonemes = set()
    while True:
        inp = input("make up a new word, enter nothing to generate a word, or enter '*' to stop\ninput: ")
        if inp == "*":
            break
        elif inp == "":
            if word_strs == []:
                print("oops! no words yet to generate from")
                continue
            while True:
                # take an existing word and replace Cs and Vs
                rws = random.choice(word_strs)
                rw = Word.from_str(rws)
                nws = ""
                for ph in rw:
                    if ph in classes["C"]:
                        cands = set(classes["C"])
                    elif ph in classes["V"]:
                        cands = set(classes["V"])
                    else:
                        raise Exception("phoneme {} is not in C or V".format(ph))
                    cands &= used_phonemes
                    nws += random.choice(list(cands))
                if nws not in word_strs:
                    break
            if input("{} : use this word? (y/n, default yes)".format(nws)) == "n":
                continue
            w = Word.from_str(nws)
        else:
            w = Word.from_str(inp)
        # w.designate(desig)
        # desig += 1
        used_phonemes |= w.get_phonemes_used()
        word_strs.append(w.to_str())
        print("current lexicon:", ", ".join(word_strs))
    return word_strs
    
def load_lexicon_from_file(fp):
    with open(fp) as f:
        lines = [x.strip() for x in f.readlines()]
    word_strs = []
    variable_segments = {}
    variable_segment_lines = [x for x in lines if ":" in x]
    lexeme_lines = [x for x in lines if ":" not in x]
    
    for line in variable_segment_lines:
        assert line.count(":") == 1, "bad line " + line
        var_name, val = line.split(":")
        if var_name in variable_segments:
            variable_segments[var_name].append(val)
        else:
            variable_segments[var_name] = [val]
            
    # print(variable_segments)
    for line in lexeme_lines:
        strs_from_line = [""]
        inside_braces = False
        variable_name = ""
        for c in line:
            if c == "{":
                assert not inside_braces
                inside_braces = True
                variable_name = ""
            elif c == "}":
                assert inside_braces
                inside_braces = False
                segment_values = variable_segments[variable_name]
                strs_from_line = [s + val for s in strs_from_line for val in segment_values]
            elif inside_braces:
                variable_name += c
            else:
                strs_from_line = [s + c for s in strs_from_line]
        word_strs += strs_from_line
    return word_strs

def get_random_unicode_character():
    n = random.randint(1, 5000)
    hex_str = str(hex(n))[2:].rjust(4, "0")
    char = eval("\"\\u{0}\"".format(hex_str))
    return char


def get_random_syllable_structure_set():
    possible_onsets = [""] * 1 + ["C"] * 4 + ["CC"] * 0
    possible_nuclei = ["V"]
    possible_codas = [""] * 4 + ["C"] * 1 + ["CC"] * 0 + ["N"] * 0 + ["NC"] * 0
    possible_structures = [onset + nucleus + coda for onset in possible_onsets for nucleus in possible_nuclei for coda in possible_codas]

    result = list(set(random.sample(possible_structures, random.randint(2, len(possible_structures)))))
    input("returning syllable structure set: {}".format(result))
    return result


def get_random_paradigm(inventory, syllable_structure_set):
    input("generating paradigm")
    root = LE2Word.get_random_phone_sequence(random.randint(1, 1), inventory, random.choice(syllable_structure_set))
    print("root:")
    root.print()
    prefixes = [LE2Word([])] + [LE2Word.get_random_phone_sequence(random.randint(1, 1), inventory, random.choice(syllable_structure_set)) for i in range(3)]
    suffixes = [LE2Word([])] + [LE2Word.get_random_phone_sequence(random.randint(1, 1), inventory, random.choice(syllable_structure_set)) for i in range(3)]
    print("prefixes:")
    for w in prefixes:
        w.print()
    print("suffixes:")
    for w in suffixes:
        w.print()
    input()
    return [prefix + root + suffix for prefix in prefixes for suffix in suffixes]


def matches_features_dict(phone, features_dict):
    if features_dict == WordBoundaryPhone().features:
        return phone == WordBoundaryPhone()
    elif type(phone) is not dict:
        return False

    for k, v in features_dict.items():
        if type(v) is list and phone[k] not in v:
            return False
        elif type(v) is not list and phone[k] != v:
            return False
    return True


def get_random_feature_value_from_inventory(inventory):
    phone = random.choice(inventory.phonemes)
    return random.choice([i for i in phone.features.items()])


def get_random_input_language():
    inventory = Inventory.random()
    syllable_structure_set = get_random_syllable_structure_set()
    phonology = Phonology(inventory, syllable_structure_set)
    vocabulary = LE2Lexicon.from_phonology(phonology)
    return (inventory, vocabulary)


def get_input_language_from_file():
    with codecs.open("LanguageEvolution2Input.txt", "rb", "utf-8") as f:
        morphemes = [x.strip() for x in f.readlines()]

    roots = [Word.from_string(x) for x in morphemes if "-" not in x]
    prefixes = [[]] + [Word.from_string(x[:-1]) for x in morphemes if x[-1] == "-"]
    suffixes = [[]] + [Word.from_string(x[1:]) for x in morphemes if x[0] == "-"]
    vocabulary = [list(prefix + root + suffix) for root in roots for prefix in prefixes for suffix in suffixes]

    inventory = []
    for word in (roots + prefixes + suffixes):
        for features_dict in word:
            if features_dict not in inventory:
                inventory.append(features_dict)

    return (inventory, vocabulary)


def generate_language_and_write_to_file():
    # original routine
    inventory, vocabulary = get_random_input_language()
    # inventory, vocabulary = get_input_language_from_file()

    text = [random.choice(vocabulary) for i in range(50)]

    epenthetic_consonant = random.choice([x for x in inventory.phonemes if x.features["syllabicity"] == 0])
    epenthetic_vowel = random.choice([x for x in inventory.phonemes if x.features["syllabicity"] == 3])

    sound_changes = [
        # ({"syllabicity": 0}, "", [WordBoundaryPhone().features], [{"syllabicity": 3}]),  # initial single consonants deleted
        # ({}, {}, {}, {}),  # do nothing
    ] + [SoundChange.get_random_sound_change_from_inventory(inventory) for i in range(30)] + [
        SoundChange({"syllabicity": 0, "voicing": 1}, {"voicing": 0}, PhoneticEnvironment([{"syllabicity": 0, "voicing": 0}], [])),
        SoundChange({"syllabicity": 0, "voicing": 1}, {"voicing": 0}, PhoneticEnvironment([], [{"syllabicity": 0, "voicing": 0}])),  # assimilate clusters to voiceless
        SoundChange("", epenthetic_vowel, PhoneticEnvironment([{"syllabicity": 0}], [{"syllabicity": 0}])),  # epenthetic vowel insertion
        SoundChange("", epenthetic_vowel, PhoneticEnvironment([WordBoundaryPhone().features, {"syllabicity": 0}], [WordBoundaryPhone().features])),  # epenthetic vowel insertion
        SoundChange("", epenthetic_consonant, PhoneticEnvironment([{"syllabicity": 3}], [{"syllabicity": 3}])),  # epenthetic consonant insertion
    ]

    fp = "LanguageEvolution2Output.txt"

    with codecs.open(fp, "wb", "utf-8") as f:
        f.write("inventory:\r\n")
        f.write(inventory.str())
        f.write("\r\n----\r\n")

        f.write("vocabulary:\r\n")
        change_dict = {}
        for word in vocabulary:
            new_word = deepcopy(word)
            for sound_change in sound_changes:
                new_word = sound_change.apply_to_word(new_word)
            ipa = word.get_ipa_str()
            new_ipa = new_word.get_ipa_str()
            change_dict[ipa] = new_ipa
            if new_ipa != ipa:
                f.write("{0} --> {1}\r\n".format(ipa, new_ipa))
            else:
                f.write("{0}\r\n".format(ipa))

        f.write("\r\n---- sample text ----\r\n")
        text_ipas = [word.get_ipa_str() for word in text]
        f.write(" ".join(text_ipas) + "\r\n-->\r\n" + " ".join([change_dict[ipa] for ipa in text_ipas]))
    print("done, written to file {}".format(fp))


def get_syllable_structures_from_user_input_words(words):
    structures = []
    for word in words:
        for syllable in word:
            raise
    # better to convert the inputted words into a canonical format usable by the lexicon


def main():
    classes = DEFAULT_PHONEME_CLASSES
    all_phonemes = set()
    for lst in classes.values():
        all_phonemes |= set(lst)
    
    test_rule_strs = ["k>t", "VCV>VsV", "Ca>za", "V#>_#", "V_V>Vju",
    ]
    daool_rule_strs = [
        "VhV>V.V",
        "#h>#_",
        "C_I>CįI",
        "C_U>CųU",
        "VCV#>VC_#",
        "VCĮV#>VCĮ_#",
        "įIV>į_V",
        "ųUV>ų_V",
        "mĮ>m_",
        "nį>n_",
        "nų>ņ_",
        "[ph]Į>f_",
        "pĮ>v_",
        "tį>r_",
        "tų>d_",
        "[th]į>č_",
        "[th]ų>t_",
        "[kh]į>s_",
        "[kh]ų>x_",
        "kį>z_",
        "kų>ğ_",
        "[tl]Į>đ_",
        "[tlh]į>þ_",
        "[tlh]ų>ď_",
        "[ts]į>[dź]_",
        "[dź]>r",
        "[ts]ų>z_",
        "[tsh]į>ć_",
        "[tsh]ų>s_",
        "sį>š_",
        "sų>s_",
        "[bh]Į>[bh]_",
        "olį>ùl_",
        "ulį>oj_",
        "lį>j_",
        "lų>l_",
        "rį>ŕ_",
        "rų>ř_",
        "jĮ>j_",
        "wĮ>w_",
        "VhĮV>V._V",
        # "#h>#_",  # already done
        "Vji>Vj_",
        "Cji>Cje",
        "#ji>#je",
        "#FaŕV>#F_ŕV",
        "VFaŕV>VF_ŕV",
        "#TaŕV>#T_ŕV",
        "ijC>i_C",
        "ijV>i.V",
        "uwC>u_C",
        "uwV>u.V",
        "i.i>i__",
        "e.e>e__",
        "u.u>u__",
        "o.o>o__",
        "a.a>a__",
    ]
    daool_rules, next_daool_rule_designation = create_rules_from_rule_strs(daool_rule_strs)
    expanded_daool_rules = []
    for r in daool_rules:
        expanded_daool_rules += r.get_specific_cases(classes, all_phonemes)
    
    # android keyboard orthography for modern Daool
    # nn ņ
    # t d, tt t
    # d ď (one char, háček)
    # v bh
    # f v, ff f
    # tl đ, ttl þ
    # s z, ss s
    # zl š
    # z ć
    # tzl č
    # x ğ, xx x
    # h .
    # rl ŕ, w ř
    # ll i/j, u u/w
    # ol ùl
    # ul oj
    
    test_word_strs = ["pak", "paka", "apak", "apaka", "limiaisa", "tr[ts]kambr", "ağ[dž]oź[dź]iuaruailiłt", "bsgrubs", "aiea", "in", "ni", "m[ts]vrtnelis[ts]qalši"]
    proto_daellic_word_strs = ["matiali", "nu", "[tlh]ia", "e[tl]aria", 
    "[ph]osati", "janio", "weli", "harai", 
    "arera", "[tsh]iari", "[tl]uli", "taholi",
    "[tlh]uelima", "ni[tlh]ue[tsh]i", "[bh]ajani", "ilisiani",
    "kiuriani", "[kh]iliu", "a[tl]uha", "se[tlh]iura",
    "[th]akariu", "liapapeti", "[kh]a[tlh]i", "luelai",
    "ilai", "[th]i", "eli[th]en", "[th]ai[tsh]a",
    "tarehe",
    ]
    verb_roots = ["tariak", "iti", "pareni", "milim"]
    #tenses = ["a", "ani", "aki"]
    subjs = ["ali", "eli", "ari", "atiali", "atieli", "atiari"]
    verb_suffixes = ["a"] + subjs
    verb_suffixes += ["anaha"] + ["ani" + x for x in subjs]
    verb_suffixes += ["akaha"] + ["aki" + x for x in subjs]
    #objs = [""]#, "api", "epi", "a[tl]i", "upi", "aumi", "umi"]
    #proto_daellic_word_strs += [r+t+s+o for r in verb_roots for t in tenses for o in objs for s in subjs]
    proto_daellic_word_strs += [r+s for r in verb_roots for s in verb_suffixes]
    #proto_daellic_word_strs = [x for x in proto_daellic_word_strs if x != ""]
    targets = ["maraj", "ņu", "þa", "eđŕa", 
    "fosar", "jano", "wej", "aři", 
    "aŕeř", "ćaŕ", "đoj", "da.ùl", 
    "ďejm", "niďeć", "[bh]ajan", "išan",
    "zuŕan", "si.u", "ađu.a", "šeþuř",
    "tağŕu", "javaver", "xaþ", "leli",
    "ili", "či", "ejčen", "tis",
    "dŕe",
    ]
    verb_roots = ["dŕağ", "ir", "vŕen", "mim"]
    #tenses = ["", "an", "az"]
    subjs = ["aj", "ej", "aŕ", "araj", "arej", "araŕ"]
    verb_suffixes = [""] + subjs
    verb_suffixes += ["aņa"] + ["an" + x for x in subjs]
    verb_suffixes += ["ağa"] + ["az" + x for x in subjs]
    #objs = [""]#, "av", "ev", "ađ", "uv", "aum", "um"]
    #targets += [r+t+s+o for r in verb_roots for t in tenses for o in objs for s in subjs]
    targets += [r+s for r in verb_roots for s in verb_suffixes]
    #targets = [x for x in targets if x != ""]
    targets += ["TODO"] * 1000 + ["END OF TARGETS"]
    
    # mode = "daool"
    # mode = "random_daellic"
    # mode = "test"
    mode = "random"
    
    def n_step_generator(n):
        for i in range(n):
            yield i
            
    def infinite_step_generator():
        i = 0
        while True:
            yield i
            i += 1
    
    if mode == "daool":
        #n_steps = len(daool_rules)
        step_generator = n_step_generator(len(daool_rules))
        word_strs = proto_daellic_word_strs
        rule_strs = daool_rule_strs
    elif mode == "test":
        #n_steps = 5
        step_generator = n_step_generator(5)
        word_strs = test_word_strs
        rule_strs = test_rule_strs
    elif mode == "random":
        #n_steps = int(input("number of steps to evolve?: "))
        step_generator = infinite_step_generator()
        if input("build lexicon from scratch? (y/n, default yes)") != "n":
            word_strs = build_lexicon_strs(classes)
        else:
            # lexicon_file = "test_lexicon.txt"
            lexicon_file = "simple_lexicon.txt"
            word_strs = load_lexicon_from_file(lexicon_file)
            print("loaded lexicon:")
            for w in word_strs:
                print("*"+w)
        rule_strs = []
    elif mode == "random_daellic":
        #n_steps = int(input("number of steps to evolve?: "))
        step_generator = infinite_step_generator()
        word_strs = proto_daellic_word_strs
        rule_strs = []
    else:
        raise Exception("invalid mode " + mode)
    
    words = [Word.from_str(s, designation=str(desig)) for desig, s in enumerate(word_strs)]
    original_words = words[:]
    next_word_designation = len(words)
    
    rules, next_rule_designation = create_rules_from_rule_strs(rule_strs, next_rule_designation=0)
    
    okay_seqs = []
    rule_history = []  # only for expanded rules
    for step_i in step_generator:
        print("\n---- step", step_i, "----\n")
        new_rules = []  # reset at every step
        used_phonemes = set()
        for w in words:
            ps = w.get_phonemes_used()
            used_phonemes |= ps
            
        try:
            rule = rules[step_i]
            print("using pre-defined rule {}".format(rule))
            expanded_rules = rule.get_specific_cases(classes, used_phonemes)
        except IndexError:
            # no pre-defined rule, so get a rule at random or from user
            print("no pre-defined rule at this step; generating random rule")
            while True:
                rule = get_random_rules(1, words, classes)[0]
                # print("{} -> {}".format(*rule))
                inp = input("is this a good rule? (default yes, n for no); or, make your own rule, e.g. m_a>mba\n")
                if ">" in inp:
                    # user made their own rule(s)
                    try:
                        rules_from_str = Rule.from_str(inp)
                        expanded_rules = []
                        for ri, rule in enumerate(rules_from_str):
                            rule.designate(str(next_rule_designation))
                            next_rule_designation += 1
                            expanded_rules += rule.get_specific_cases(classes, used_phonemes)
                            print("expanded_rules now has len", len(expanded_rules))
                        print("got user rules in new-step phase:", rules_from_str)

                        # ensure that used phonemes will contain anything new created by the rule
                        for r in expanded_rules:
                            used_phonemes |= set(r.get_output_phonemes_used())
                        #expanded_rules = parse_rule_str(inp, classes, used_phonemes)
                        break
                    except AssertionError:
                        print("invalid rule input")
                elif inp != "n":
                    # the given rule was accepted
                    # give it a designation
                    rule.designate(str(next_rule_designation))
                    next_rule_designation += 1
                    expanded_rules = rule.get_specific_cases(classes, used_phonemes)
                    break
                else:
                    # user rejected rule
                    continue
                    
        n_main_rules = len(expanded_rules)
        
        all_rules_this_round = expanded_rules
        rule_catchup_tracker = [-1 for r in expanded_rules]  
        # if get new rule from user, add a term here and start at beginning of list of words, applying all user rules that have not been applied yet
        # e.g. [5] indicating word_i 5 has had the main rule applied, user makes a new rule
        # then [5, -1], then start at word_i 0 again
        # suppose at word_i 2 on this second sweep, user makes another rule
        # then [5, 2, -1], then user makes no more rules this round
        # for word_i, if array element is less than word_i then rule has not been applied, so apply it
        
        word_i = 0
        new_words = [None] * len(words)
        while True:
            #print("sleepy time")
            #time.sleep(1)
            word = words[word_i]
            #print("processing word #{}, {}\nrules: {}\ntracker: {}".format(word_i, word, all_rules_this_round, rule_catchup_tracker))
            
            new_rules = []  # clear it so things won't be overwritten if user makes yet another rule this step (i.e. there will be a third "start" (word_i=0) to this while loop)
            assert len(all_rules_this_round) == len(rule_catchup_tracker), "{} rules but tracker has {}".format(len(all_rules_this_round), len(rule_catchup_tracker))
            rule_indices_to_apply = [ri for ri in range(len(all_rules_this_round)) if rule_catchup_tracker[ri] < word_i]
            rules_to_apply = [all_rules_this_round[ri] for ri in rule_indices_to_apply]
            #inputs_with_effect = get_inputs_that_could_apply(word)
            rules_to_apply_with_effect = rules_to_apply #[r for r in rules_to_apply if [x for x in r[0] if x != ""] in inputs_with_effect]
            #print(word, inputs_with_effect, rules_to_apply_with_effect)
            new_word = evolve_word(word, rules_to_apply_with_effect)
            for ri in rule_indices_to_apply:
                assert rule_catchup_tracker[ri] == word_i - 1, "word_i {}, error in tracker {}".format(word_i, rule_catchup_tracker)  # didn't miss anybody in between
                rule_catchup_tracker[ri] = word_i
            #assert all(x >= word_i - 1 for x in rule_catchup_tracker), "word_i: {}; rule catchup tracker: {}".format(word_i, rule_catchup_tracker)
            # evolve_word should print if a change is made
            #print("word is now",new_word)
            words[word_i] = new_word  # update before cleanup so it will be saved with whatever change just happened
            if mode != "daool":
                new_word, okay_seqs, new_rules = cleanup(new_word, classes, okay_seqs, new_rules, used_phonemes)
                #print("cleanup results:\n{}\n{}\n{}".format(new_word, okay_seqs, new_rules))
                #input("continue")
                # if get okay seqs, no need to backtrack, just don't ask about them again this step_i
            
                words[word_i] = new_word # replace a None if not evolved yet, replace old version if doing rule catchup
            
            # if got some more user rules
            expanded_new_rules = []
            for r in new_rules:
                r.designate(str(next_rule_designation))
                next_rule_designation += 1
                expanded_new_rules += r.get_specific_cases(classes, used_phonemes)
            
            for r in expanded_new_rules:
                print("appending to rules this round:", r)
                all_rules_this_round.append(r)
                rule_catchup_tracker.append(-1)
                
            # new_rules = expanded_new_rules
            # if n_main_rules + len(new_rules) > len(rule_catchup_tracker):
                # print("new rules!")
                # print(new_rules)
                # rule_catchup_tracker += [-1] * (n_main_rules + len(new_rules) - len(rule_catchup_tracker))
            if len(expanded_new_rules) > 0:
                # go back to first word and apply these new rule
                print("resetting to word_i 0 to apply new rules")
                word_i = 0
                continue
            else:
                pass #print("nothing new under the sun")
                
            word_i += 1
            if word_i >= len(words):
                break
                
        # after finish while loop, check that everyone got all the rules
        assert all(x == len(words) - 1 for x in rule_catchup_tracker)
        rule_history += all_rules_this_round[:]
                
        #words = new_words
        print("---- finished with step {} ----".format(step_i))
        if any(len(w) < 1 for w in words):
            raise IndexError("blank words created")
            
        print("\n\nlexicon after step", step_i)
        for ow, w, target in zip(original_words, words, targets):
            report = "*{}".format(ow.to_str())
            if ow == w:
                report += " ==="
            else:
                report += " -> " + w.to_str()
            if mode in ["daool", "random_daellic"]:
                report += " (Daool {})".format(target)
            print(report)
            
        if mode in ["random", "random_daellic"]:
            new_proto_words = evolve_user_input_words(rule_history, expanded_daool_rules, words)
            original_words += new_proto_words
            words += [evolve_word(w, rule_history) for w in new_proto_words]
        if mode != "daool" and input("press enter to continue, or enter '*' to stop: ") == "*":
            break
            
    if mode == "daool":
        print("\nchecking Daool evolution")
        errors = 0
        for word, target in zip(words, targets):
            target = Word.from_str(target)
            if word != target:
                print("result {} != target {}".format("".join(word), target))
                errors += 1
        print("{} errors found".format(errors))
    else:
        print("\nnot checking Daool evolution")
        
    print("rule history")
    for r in rule_history:
        print(r)


if __name__ == "__main__":    
    main()
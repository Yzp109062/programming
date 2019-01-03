import codecs
import itertools
import os
import pickle
import random

from copy import deepcopy



def restrict_features(features):
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

    return features


def get_features_from_ipa_symbol(symbol):
    return IPA_SYMBOL_TO_FEATURES[symbol]


def get_word_from_string(s):
    word = []
    for symbol in s:
        if symbol not in ["-", "\ufeff"]:
            features_dict = get_features_from_ipa_symbol(symbol)
            word.append(features_dict)
    return word


def get_ipa_symbol_from_features(features):
    if type(features) is not dict:
        return ""

    features = restrict_features(features)

    if features["syllabicity"] == 0:
        return get_ipa_consonant_symbol_from_features(features)

    if features["syllabicity"] == 1:
        return get_ipa_vowel_symbol_from_features(features) + "\u032f"

    if features["syllabicity"] == 2:
        return get_ipa_consonant_symbol_from_features(features) + "\u0329"

    elif features["syllabicity"] == 3:
        return get_ipa_vowel_symbol_from_features(features)


def get_ipa_consonant_symbol_from_features(features, with_secondaries=True):
    # code = get_numerical_code_from_features(features)
    code = "_"
    secondaries = get_secondary_symbols_from_features(features) if with_secondaries else ""

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
        plosive_symbol = get_ipa_consonant_symbol_from_features(plosive_features, with_secondaries=False)

        fricative_features = deepcopy(features)
        fricative_features["c_manner"] = 2
        fricative_symbol = get_ipa_consonant_symbol_from_features(fricative_features, with_secondaries=False)

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


def get_ipa_vowel_symbol_from_features(features, with_secondaries=True):
    # code = get_numerical_code_from_features(features)
    code = "_"
    secondaries = get_secondary_symbols_from_features(features) if with_secondaries else ""

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


def get_numerical_code_from_features(features):
    # return "_"
    # return repr(features)
    return "\n\n<?" + ",".join([str(v) for k, v in sorted(features.items())]) + ">\n\n"


def get_random_unicode_character():
    n = random.randint(1, 5000)
    hex_str = str(hex(n))[2:].rjust(4, "0")
    char = eval("\"\\u{0}\"".format(hex_str))
    return char


def get_random_features():
    d = {}
    for k, v in FEATURE_KEYS.items():
        d[k] = random.choice([x for x in v.keys()])
    return d


def get_features_from_possible_values(feature_value_sets):
    d = {}
    for k, v in FEATURE_KEYS.items():
        d[k] = random.choice([x for x in feature_value_sets[k]])
    return d


def get_random_feature_value_sets():
    value_probabilities = {
        "c_aspiration": [1, 0.3],
        "c_glottalization": [1, 0],
        "c_labialization": [1, 0],
        "c_lateralization": [1, 0.5],
        "c_manner": [1, 0.5, 0.7, 0.7],
        "c_palatization": [1, 0.3],
        "c_pharyngealization": [1, 0.1],
        "c_place": [0.5, 0.1, 0.1, 0.8, 0.3, 0.4, 0.4, 1, 0.3, 0.1, 0.05, 0.5],
        "c_velarization": [1, 0.2],
        "length": [1, 0.2],
        "nasalization": [1, 0.2],
        "syllabicity": [1, 0.05, 0.2, 1],
        "v_backness": [1, 0.5, 0.9],
        "v_height": [1, 0.2, 0.5, 0.5, 0.5, 0.2, 0.9],
        "v_roundedness": [1, 0.8],
        "voicing": [1, 0.5],
    }

    d = {}
    for k, v in FEATURE_KEYS.items():
        d[k] = []
        for val in v.keys():
            if random.random() < value_probabilities[k][val]:
                d[k].append(val)
    return d


def get_random_inventory():
    phonology = get_random_feature_value_sets()
    raw_inventory = [get_features_from_possible_values(phonology) for i in range(40)]
    seen = []
    seen_symbols = []
    for phone in raw_inventory:
        restricted_phone = restrict_features(phone)
        symbol = get_ipa_symbol_from_features(restricted_phone)
        if symbol not in seen_symbols and "_" not in symbol and "?" not in symbol:
            seen.append(restricted_phone)
            seen_symbols.append(symbol)
    return seen


def get_random_syllable_structure_set():
    possible_onsets = [""] * 3 + ["C"] * 4 + ["CC"] * 1
    possible_nuclei = ["V"]
    possible_codas = [""] * 4 + ["C"] * 2 + ["CC"] * 1 + ["N"] * 2 + ["NC"] * 1
    possible_structures = [onset + nucleus + coda for onset in possible_onsets for nucleus in possible_nuclei for coda in possible_codas]

    return list(set(random.sample(possible_structures, random.randint(2, len(possible_structures)))))


def get_random_phone_sequence(n_syllables, inventory, syllable_structure):
    result = []
    for i in range(n_syllables):
        for typ in syllable_structure:
            if typ == "C":
                cands = [x for x in inventory if x["syllabicity"] in [0, 1]]
                chosen = random.choice(cands) if cands != [] else None
            elif typ == "V":
                cands = [x for x in inventory if x["syllabicity"] in [2, 3]]
                chosen = random.choice(cands) if cands != [] else None
            elif typ == "N":
                cands = [x for x in inventory if x["syllabicity"] == 0 and x["nasalization"] == 1 and x["c_manner"] == 0]
                chosen = random.choice(cands) if cands != [] else None
            else:
                chosen = random.choice(inventory)

            if chosen is not None:
                result.append(chosen)
    return result


def convert_phone_sequence_to_ipa(seq):
    result = ""
    for phone in seq:
        result += get_ipa_symbol_from_features(phone)
    return result


def get_random_paradigm(inventory, syllable_structure_set):
    root = get_random_phone_sequence(random.randint(1, 1), inventory, random.choice(syllable_structure_set))
    prefixes = [[]] + [get_random_phone_sequence(random.randint(1, 1), inventory, random.choice(syllable_structure_set)) for i in range(3)]
    suffixes = [[]] + [get_random_phone_sequence(random.randint(1, 1), inventory, random.choice(syllable_structure_set)) for i in range(3)]
    return [prefix + root + suffix for prefix in prefixes for suffix in suffixes]


def get_random_vocabulary(inventory, syllable_structure_set):
    vocabulary = []
    for i in range(50):
        paradigm = get_random_paradigm(inventory, syllable_structure_set)
        for word in paradigm:
            vocabulary.append(word)
    return vocabulary


def matches_features_dict(phone, features_dict):
    if features_dict == "#":
        return phone == "#"
    elif type(phone) is not dict:
        return False

    for k, v in features_dict.items():
        if type(v) is list and phone[k] not in v:
            return False
        elif type(v) is not list and phone[k] != v:
            return False
    return True


def apply_sound_change_to_word(sound_change, word):
    from_features, to_features, before_features_list, after_features_list = sound_change

    if from_features == "" and to_features == "":
        return word

    word = ["#"] + word + ["#"]

    before_len = len(before_features_list)
    start_index = before_len
    after_len = len(after_features_list)
    end_index_exclusive = len(word) - after_len

    new_word = []

    if type(from_features) is dict:
        for i, phone in enumerate(word):
            if i < before_len or i >= end_index_exclusive:
                new_word.append(deepcopy(phone))
                continue

            before_environment = word[i - before_len: i]
            after_environment = word[i + 1: i + after_len + 1]

            matches_phone = matches_features_dict(phone, from_features)
            if not matches_phone:
                new_word.append(deepcopy(phone))
                continue

            matches_before = all([matches_features_dict(before_environment[j], before_features_list[j]) for j in range(before_len)])
            matches_after = all([matches_features_dict(after_environment[j], after_features_list[j]) for j in range(after_len)])
            if matches_before and matches_after:
                if to_features == "":
                    new_word.append(None)
                else:
                    new_phone = deepcopy(phone)
                    new_phone.update(to_features)
                    new_word.append(new_phone)
            else:
                new_word.append(deepcopy(phone))

    elif from_features == "":
        for i, phone in enumerate(word):
            if i < before_len or i >= end_index_exclusive:
                new_word.append(deepcopy(phone))
                continue

            before_environment = word[i - before_len: i]
            after_environment = word[i: i + after_len]

            matches_before = all([matches_features_dict(before_environment[j], before_features_list[j]) for j in range(before_len)])
            matches_after = all([matches_features_dict(after_environment[j], after_features_list[j]) for j in range(after_len)])
            if matches_before and matches_after:
                new_phone = DEFAULT_FEATURE_VALUES
                new_phone.update(to_features)
                new_word.append(new_phone)
                new_word.append(deepcopy(phone))
            else:
                new_word.append(deepcopy(phone))

    else:
        raise ValueError("invalid from_features: {0}".format(from_features))

    return [x for x in new_word if x is not None]


def get_random_feature_value_from_inventory(inventory):
    phone = random.choice(inventory)
    return random.choice([i for i in phone.items()])


def get_random_sound_change(inventory):
    feature, value = get_random_feature_value_from_inventory(inventory)
    feature2, value2 = get_random_feature_value_from_inventory(inventory)
    feature3, value3 = get_random_feature_value_from_inventory(inventory)
    feature4, value4 = get_random_feature_value_from_inventory(inventory)

    from_features = {feature: value} if random.random() < 0.95 else ""
    to_features = {feature2: random.choice([i for i in FEATURE_KEYS[feature2].keys()])} if random.random() < 0.95 else ""
    before_environment = {feature3: value3} if random.random() < 0.8 else "#"
    after_environment = {feature4: value4} if random.random() < 0.8 else "#"

    return (from_features, to_features, [before_environment], [after_environment])


def get_random_input_language():
    inventory = get_random_inventory()
    syllable_structure_set = get_random_syllable_structure_set()
    vocabulary = get_random_vocabulary(inventory, syllable_structure_set)
    return (inventory, vocabulary)


def get_input_language_from_file():
    with codecs.open("LanguageEvolution2Input.txt", "rb", "utf-8") as f:
        morphemes = [x.strip() for x in f.readlines()]

    roots = [get_word_from_string(x) for x in morphemes if "-" not in x]
    prefixes = [[]] + [get_word_from_string(x[:-1]) for x in morphemes if x[-1] == "-"]
    suffixes = [[]] + [get_word_from_string(x[1:]) for x in morphemes if x[0] == "-"]
    vocabulary = [list(prefix + root + suffix) for root in roots for prefix in prefixes for suffix in suffixes]

    inventory = []
    for word in (roots + prefixes + suffixes):
        for features_dict in word:
            if features_dict not in inventory:
                inventory.append(features_dict)

    return (inventory, vocabulary)


# ---- constructing global constants ---- #

FEATURE_KEYS = {
    "c_aspiration": {0: "non-aspirated", 1: "aspirated"},
    "c_glottalization": {0: "non-glottalized", 1: "glottalized"},
    "c_labialization": {0: "non-labialized", 1: "labialized"},
    "c_lateralization": {0: "non-lateral", 1: "lateral"},
    "c_manner": {0: "stop", 1: "affricate", 2: "fricative", 3: "approximant"},
    "c_palatization": {0: "non-palatized", 1: "palatized"},
    "c_pharyngealization": {0: "non-pharyngealized", 1: "pharyngealized"},
    "c_place": {0: "bilabial", 1: "labiodental", 2: "dental", 3: "alveolar", 4: "postalveolar", 5: "retroflex", 6: "palatal", 7: "velar", 8: "uvular", 9: "pharyngeal", 10: "epiglottal", 11: "glottal"},
    "c_velarization": {0: "non-velarized", 1: "velarized"},
    "length": {0: "normal", 1: "long"},
    "nasalization": {0: "non-nasalized", 1: "nasalized"},
    "syllabicity": {0: "consonant", 1: "non-syllabic vowel", 2: "syllabic consonant", 3: "vowel"},
    "v_backness": {0: "front", 1: "central", 2: "back"},
    "v_height": {0: "open", 1: "near-open", 2: "open-mid", 3: "mid", 4: "close-mid", 5: "near-close", 6: "close"},
    "v_roundedness": {0: "unrounded", 1: "rounded"},
    "voicing": {0: "voiceless", 1: "voiced"},
}


DEFAULT_FEATURE_VALUES = {k: 0 for k in FEATURE_KEYS.keys()}


def get_ipa_symbol_to_features_dict():
    if os.path.isfile("C:/Users/Wesley/Desktop/Programming/IPA_SYMBOL_TO_FEATURES.pickle"):
        with open("C:/Users/Wesley/Desktop/Programming/IPA_SYMBOL_TO_FEATURES.pickle", "rb") as f:
            d = pickle.load(f)
        return d

    else:
        def my_product(dicts):
            # http://stackoverflow.com/questions/5228158/cartesian-product-of-a-dictionary-of-lists
            return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))

        d = {k: sorted(v.keys(), reverse=True) for k, v in FEATURE_KEYS.items()}
        n = 1
        for lst in d.values():
            n *= len(lst)
        input("total symbol-dict pairs to compute: {0}\npress enter to continue".format(n))

        result = {}
        i = 0
        for features_dict in my_product(d):
            features_dict = restrict_features(features_dict)
            i += 1
            if i % 10000 == 0:
                print(i)
            symbol = get_ipa_symbol_from_features(features_dict)
            result[symbol] = features_dict

        with open("C:/Users/Wesley/Desktop/Programming/IPA_SYMBOL_TO_FEATURES.pickle", "wb") as f:
            pickle.dump(result, f, pickle.HIGHEST_PROTOCOL)

        return result


IPA_SYMBOL_TO_FEATURES = get_ipa_symbol_to_features_dict()

COMMON_SOUND_CHANGES = [
    ({"voicing": 0}, {"voicing": 1}, [{"syllabicity": 3}], [{"syllabicity": 3}]),  # intervocalic voicing
    ({"syllabicity": 3}, {"v_backness": 2}, [{"syllabicity": [0, 2], "c_place": [8, 9, 10, 11]}], []),  # vowels move back after uvulars+
]



if __name__ == "__main__":
    inventory, vocabulary = get_random_input_language()
    # inventory, vocabulary = get_input_language_from_file()

    text = [random.choice(vocabulary) for i in range(50)]

    epenthetic_consonant = random.choice([x for x in inventory if x["syllabicity"] == 0])
    epenthetic_vowel = random.choice([x for x in inventory if x["syllabicity"] == 3])

    sound_changes = [
        # ({"syllabicity": 0}, "", ["#"], [{"syllabicity": 3}]),  # initial single consonants deleted
        # ({}, {}, {}, {}),  # do nothing
    ] + [get_random_sound_change(inventory) for i in range(30)] + [
        ({"syllabicity": 0, "voicing": 1}, {"voicing": 0}, [{"syllabicity": 0, "voicing": 0}], []),
        ({"syllabicity": 0, "voicing": 1}, {"voicing": 0}, [], [{"syllabicity": 0, "voicing": 0}]),  # assimilate clusters to voiceless
        ("", epenthetic_vowel, [{"syllabicity": 0}], [{"syllabicity": 0}]),  # epenthetic vowel insertion
        ("", epenthetic_vowel, ["#", {"syllabicity": 0}], ["#"]),  # epenthetic vowel insertion
        ("", epenthetic_consonant, [{"syllabicity": 3}], [{"syllabicity": 3}]),  # epenthetic consonant insertion
    ]

    with codecs.open("LanguageEvolution2Output.txt", "wb", "utf-8") as f:
        f.write("inventory:\r\n")
        f.write("  ".join([get_ipa_symbol_from_features(x) for x in sorted(inventory, key=lambda x: get_numerical_code_from_features(x))]))
        f.write("\r\n----\r\n")

        f.write("vocabulary:\r\n")
        change_dict = {}
        for word in vocabulary:
            new_word = deepcopy(word)
            for sound_change in sound_changes:
                new_word = apply_sound_change_to_word(sound_change, new_word)
            ipa = convert_phone_sequence_to_ipa(word)
            new_ipa = convert_phone_sequence_to_ipa(new_word)
            change_dict[ipa] = new_ipa
            if new_ipa != ipa:
                f.write("{0} --> {1}\r\n".format(ipa, new_ipa))
            else:
                f.write("{0}\r\n".format(ipa))

        f.write("\r\n---- sample text ----\r\n")
        text_ipas = [convert_phone_sequence_to_ipa(word) for word in text]
        f.write(" ".join(text_ipas) + "\r\n-->\r\n" + " ".join([change_dict[ipa] for ipa in text_ipas]))


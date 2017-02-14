from datetime import datetime
import os
import pickle
import random
import time

import pygame
import pygame.midi as midi
midi.init()

import Music.MusicalStructureUtil as structure


def get_input_and_output_devices():
    # Casio LK-43
    CASIO_KEYBOARD_NAME = b"UM-2"  # two inputs, each with this name, 
    CASIO_KEYBOARD_OTHER_NAME = b"MIDIOUT2 (UM-2)"

    infos = [midi.get_device_info(device_id) for device_id in range(midi.get_count())]
    # print(infos)

    input_device_id = None
    output_device_id = None
    alt_device_id = None
    for device_id, info in enumerate(infos):
        interf, name, is_input, is_output, is_opened = info
        if name == CASIO_KEYBOARD_NAME:
            if is_input:
                input_device_id = device_id
            elif is_output:
                output_device_id = device_id
        elif name == CASIO_KEYBOARD_OTHER_NAME:
            alt_device_id = device_id

    # print(input_device_id, output_device_id)

    inp = midi.Input(input_device_id)
    outp = midi.Output(output_device_id)

    return inp, outp


def send_data_to_midi_out(data, midi_output):
    midi_output.write(data)


def send_notes_to_midi_out(notes, midi_output):
    for note in notes:
        assert type(note) in [structure.Note, structure.Chord, structure.Rest], (
            "note must be Music\\MusicalStructureUtil.Note or Chord, not {}. object received: {}".format(type(note), note)
        )
        note.output_to_midi(midi_output)


def read_data_from_midi_in(midi_input):
    data = []
    t0 = time.time()
    timeout_seconds = 1
    while time.time() - t0 < timeout_seconds:
        if midi_input.poll():
            new_data = midi_input.read(1)
            assert len(new_data) == 1
            new_data = new_data[0]
            data.append(new_data)
            print(new_data)
            lst, timestamp = new_data
            status, data1, data2, data3 = lst
            pitch = data1
            event = data2
            event_name = "note_on" if data2 == 75 else "note_off" if data2 == 0 else "unknown_event"
            # ? = data3
    return data


def read_notes_from_midi_in(midi_input):
    data = read_data_from_midi_in(midi_input)
    # TODO: parse data
    raise NotImplementedError


def dump_data(data):
    now_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    with open("Music\\midi_input_{}.pickle".format(now_str), "wb") as f:
        pickle.dump(data, f)


def load_random_data():
    data_dir = "Music\\"
    ls = os.listdir(data_dir)
    choices = [x for x in filter(lambda x: x.startswith("midi_input_"), ls)]
    print(choices)
    choice = random.choice(choices)
    with open(data_dir + choice, "rb") as f:
        data = pickle.load(f)
    return data


if __name__ == "__main__":
    try:
        inp, outp = get_input_and_output_devices()
        print(inp, outp)

        # notes = read_notes_from_midi_in(inp)

        # data = read_data_from_midi_in(inp)
        # dump_data(data)

        data = load_random_data()
        send_data_to_midi_out(data, outp)

    except:
        raise
    finally:
        inp.close()
        outp.close()
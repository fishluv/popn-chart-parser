from parse_chart import get_events

"""
Merge two sorted iterables based on some comparison predicate.
If the predicate returns the same value for each iterable, prefer the first.
"""
def _merge(first, second, cmp):
  out = []
  i_first, i_second = 0, 0
  while i_first < len(first) and i_second < len(second):
    next_first = first[i_first] 
    next_second = second[i_second]
    # Prefer first for equality.
    if cmp(next_first) <= cmp(next_second):
      out.append(next_first)
      i_first += 1
    else:
      out.append(next_second)
      i_second += 1
  out += first[i_first:]
  out += second[i_second:]
  return out

"""
Disables/autoplays keysounds for a chart.

Accomplishes this by converting `loadsample` commands into `playsample` commands.

Usage:
  python autoplay_keysounds.py --bin-in-file sorasumi_op.bin --bin-out-file sorasumi_op_new.bin
"""
if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("-b", "--bin-in-file", required=True)
  parser.add_argument("-o", "--bin-out-file", required=True)
  args = parser.parse_args()

  bin_in_file = args.bin_in_file
  bin_out_file = args.bin_out_file

  if bin_in_file == bin_out_file:
    print("Not recommended to output to (and effectively overwrite) input bin file.")
    exit(1)

  old_events = get_events(bin_in_file)
  old_events_without_loadsample = [event for event in old_events if event[1] != "loadsample"]

  first_key_timestamp = next(event for event in old_events if event[1] == "key")[0]
  # All charts (even non-keysounded ones) have 9 loadsample events somewhere between 130-250 ms before the first key event.
  # One loadsample event for each key. Some of these events load sample 0 (necessary dummy events) but others are real.
  # In the output chart we just want 9 dummy events, with sample index 0.
  # loadsample values are calculated by `key << 12 | sample_idx` but since sample_idx is 0 we can just do `key << 12`.
  new_dummy_loadsample_events = [(first_key_timestamp - 200, "loadsample", key << 12, 0) for key in range(9)]

  # Generate new playsample events from existing loadsample and key events.
  new_playsample_events = []
  loaded_sample_for_key = [0, 0, 0, 0, 0, 0, 0, 0, 0]
  for timestamp, event_name, event_value, _ in old_events:
    if event_name == "key":
      key = event_value & 0xff
      if loaded_sample_for_key[key] == 0: # Ignore un-keysounded notes.
        continue

      playsample_val = (8 << 12) | loaded_sample_for_key[key] # Purpose of `8` is unknown but all playsample events have it.
      new_playsample_events.append((timestamp, "playsample", playsample_val, 0))

    if event_name == "loadsample":
      key, sample_idx = event_value >> 12, event_value & 0xff
      if sample_idx == 0: # Ignore dummy loadsample events at beginning of chart.
        continue

      loaded_sample_for_key[key] = sample_idx

  new_events = _merge(new_dummy_loadsample_events, new_playsample_events, lambda event: event[0])
  # Put new playsample events before matching key events.
  # Not sure how important this is but this is what popnhax does.
  final_events = _merge(new_events, old_events_without_loadsample, lambda event: event[0])

  event_name_to_id = {
    "key": 0x0145,
    "loadsample": 0x0245,
    "playbgsample": 0x0345,
    "bpm": 0x0445,
    "timesig": 0x0545,
    "end": 0x0645,
    "playsample": 0x0745,
    "timing": 0x0845,
    "unk0945": 0x0945,
    "unk0d45": 0x0d45,
    "measure": 0x0a00,
    "beat": 0x0b00,
    "unk000f": 0x000f,
  }

  with open(bin_out_file, "wb") as f:
    for timestamp, event_name, event_value, _ in final_events:
      f.write(timestamp.to_bytes(4, byteorder="little"))
      f.write(event_name_to_id[event_name].to_bytes(2, byteorder="little"))
      f.write(event_value.to_bytes(2, byteorder="little"))

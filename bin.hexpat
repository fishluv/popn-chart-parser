/*
 * ImHex pattern file for pop'n music bin files.
 *
 * Usage: Open bin file in ImHex. Then paste the contents of
 * this file into the pattern editor panel.
 */

#pragma endian little

#include "std/core"
#include "std/io"

enum EventType: u16 {
    Key = 0x0145,
    Sample = 0x0245,
    Bpm = 0x0445,
    TimeSig = 0x0545,
    End = 0x0645,
    Sample2 = 0x0745,
    Timing = 0x0845,
    Measure = 0x0a00,
    Beat = 0x0b00,
};

fn formatNote(u8 note) {
    match (note) {
        (0): return "1 (left white)";
        (1): return "2 (left yellow)";
        (2): return "3 (left green)";
        (3): return "4 (left blue)";
        (4): return "5 (red)";
        (5): return "6 (right blue)";
        (6): return "7 (right green)";
        (7): return "8 (right yellow)";
        (8): return "9 (right white)";
        (_): return str(note);
    }
};

struct Key {
    u8 note [[format("formatNote")]];
    padding[1];
} [[color("ff0000")]];

fn formatSample(u16 sample) {
    u8 keysound = sample & 0xfff;
    u8 note = sample >> 12;
    return std::format("keysound {}, note {}", keysound, formatNote(note));
};

struct Sample {
    u16 sample [[format("formatSample")]];
} [[color("00ff00")]];

struct Bpm {
    u16 bpm;
} [[color("2288ff")]];

fn formatSignature(u16 sig) {
    u8 bottom = sig & 0xff;
    u8 top = sig >> 8 & 0xff;
    return std::format("{}/{}", top, bottom);
};

struct TimeSig {
    u16 signature [[format("formatSignature")]];
} [[color("228888")]];

struct End {
    u16 end;
} [[color("222222")]];

fn formatSample2(u16 sample2) {
    return std::format("keysound {}", sample2 & 0xfff);
};

struct Sample2 {
    u16 sample2 [[format("formatSample2")]];
} [[color("ffff00")]];

fn formatTiming(u16 timing) {
    u8 val = timing & 0xff;
    u8 idx = timing >> 12;
    if (idx == 0) {
        return std::format("early bad: {}", val);
    } else if (idx == 1) {
        return std::format("early good: {}", val);
    } else if (idx == 2) {
        return std::format("early great: {}", val);
    } else if (idx == 3) {
        return std::format("late great: {}", val);
    } else if (idx == 4) {
        return std::format("late good: {}", val);
    } else if (idx == 5) {
        return std::format("late bad: {}", val);
    } else {
        return str(timing);
    }
};

struct Timing {
    u16 timing [[format("formatTiming")]];
} [[color("882288")]];

struct Measure {
    u16 measure;
} [[color("666666")]];

struct Beat {
    u16 beat;
} [[color("aaaaaa")]];

fn formatTimestamp(u32 timestamp) {
    u32 ms = timestamp % 1000;
    u32 totalSec = timestamp / 1000;
    u32 sec = totalSec % 60;
    u32 min = totalSec / 60;
    return std::format("{0}:{1:02d}.{2:03d}", min, sec, ms);
};

struct Event {
    u32 timestamp [[color("dddddd"), format("formatTimestamp")]];
    EventType type [[hidden]];
    match (type) {
        (EventType::Key): Key [[inline]];
        (EventType::Sample): Sample [[inline]];
        (EventType::Bpm): Bpm [[inline]];
        (EventType::TimeSig): TimeSig [[inline]];
        (EventType::End): End [[inline]];
        (EventType::Sample2): Sample2 [[inline]];
        (EventType::Timing): Timing [[inline]];
        (EventType::Measure): Measure [[inline]];
        (EventType::Beat): Beat [[inline]];
        (_): u16 eventValue;
    }
    if (!isOldFormat) {
        u32 length [[color("dddddd"), format("formatTimestamp")]];
    }
} [[name(type)]];

struct Main {
    Event events[while(!std::mem::eof())] [[inline]];
};

u64 isOldFormat @ 0x08;
Main m @ 0x0 [[inline]];

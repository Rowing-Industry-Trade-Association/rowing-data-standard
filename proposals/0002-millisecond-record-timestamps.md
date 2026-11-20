# 0002 — Millisecond record timestamps

| | |
|---|---|
| **Status** | draft |
| **Author** | Joris Blaak |
| **Created** | 2026-11-20 |
| **Issue** | #69 |
| **Targets** | spec §4, §5.1 · field ID 97 |
| **Objection window closes** | 2026-12-04 (≥ 14 days after visibility) |

## Problem

The native FIT `timestamp` on a Record is a whole number of seconds. With
stroke-boundary recording (§2.2) a stroke almost never ends on a whole second,
so every record's time is wrong by up to 999 ms. When a stroke is shorter than a
second, two records can have the same timestamp.

So a consumer cannot rebuild the time series of a workout from the file. Stroke
periods taken from consecutive timestamps jump by whole seconds. Adding up
`StrokeDriveTime` and `StrokeRecoveryTime` instead drifts, and it breaks at
every pause. Time-sampled recording (§2.4) faster than 1 Hz has the same
problem: several records share one timestamp, and only their order tells them
apart.

The devices already know the time to the millisecond. The RP3 and WaterRower
devices both record at that precision, and it is lost when they write the FIT
file.

## Proposal

Add one record-level developer field that carries the milliseconds the native
`timestamp` cannot hold.

| Message | ID | Name | Base type | Scale | Units | Definition | Typical range |
|---|---|---|---|---|---|---|---|
| record | 97 | `TimestampMs` | UINT16 | 1 | ms | Milliseconds past the whole second in the record's native `timestamp`. The record time is `timestamp` + `TimestampMs` / 1000 s | 0–999 |

The time is truncated, not rounded. A record at 12:00:05.999 is written as
`timestamp` 12:00:05 and `TimestampMs` 999, never as 12:00:06 and 0. That keeps
`timestamp` the whole-second floor of the true time, so a reader that uses only
`timestamp` and a reader that uses both always agree on which second a record is
in.

- **Absent behaviour** — the record time is `timestamp`, to the whole second, as
  it is today.
- **Unaware behaviour** — a consumer that does not know field 97 ignores it, as
  it does any unknown developer field, and reads `timestamp`, which is at most
  999 ms early.
- **RFC 2119 level** — producers SHOULD write it when they know the record time
  to better than a second, and MUST truncate. SHOULD rather than MUST, because a
  GPS watch writing at whole-second updates has nothing to add. Consumers that
  use time SHOULD add it to `timestamp`. Consumers MUST treat a value of 1000 or
  more as missing, since it would make `timestamp` no longer the whole second.

## Spec text

In the §4 native field table, the `timestamp` row becomes:

> | timestamp | UINT32 | Record timestamp | Seconds since Garmin epoch (1989-12-31 UTC). The milliseconds go in TimestampMs (§5.1) |

In the §5.1 table, after StrokeState:

> | TimestampMs | 97 | UINT16 | 1 | ms | Milliseconds past the whole second in the record's native `timestamp` | 0-999 ms |

And in the §5.1 notes:

> - **TimestampMs**: The millisecond part of the record time, which is
>   `timestamp` + TimestampMs / 1000 s. Producers SHOULD write it when they know
>   the record time to better than a second. They MUST truncate the time, not
>   round it, so that `timestamp` is never later than the true time: a record at
>   12:00:05.999 is written as `timestamp` 12:00:05 and TimestampMs 999, not as
>   12:00:06 and 0. Consumers SHOULD add it to `timestamp` when they use the
>   record time. Values of 1000 and above are invalid, and consumers MUST treat
>   them as missing. When TimestampMs is absent, the record time is `timestamp`,
>   to the whole second.

In `registry/field-ids.md`, ID 97 is assigned to `TimestampMs`, and the native
`timestamp` row points to it.

## Compatibility

- **Existing files** — no conforming file becomes non-conforming or changes
  meaning. The field is new and optional.
- **Existing consumers** — a consumer built against 1.0-RC ignores field 97 and
  reads the whole-second `timestamp`, as it does today.
- **Migration** — none. Nothing is replaced.

## Alternatives considered

- **Do nothing.** Consumers keep deriving time from drive and recovery times,
  which drifts and breaks at every pause, and time-sampled files above 1 Hz keep
  records that share a timestamp.
- **A native FIT field.** The FIT profile has sub-second time fields
  (`timestamp_ms`, `fractional_timestamp`) on some other messages, but not on
  Record, so there is no native field for producers to use.
- **Scale 32768 (1/32768 s)**, as FIT's `fractional_timestamp` uses. Finer than
  any rowing device measures, and harder to read than milliseconds, which the
  devices already use and which every other time field in this standard
  (`StrokeDriveTime`, `StrokeRecoveryTime`) is in.
- **Rounding to the nearest second.** Rounding moves a record into the next
  second, so the whole-second `timestamp` and the full time can disagree about
  which second a record is in. Truncating avoids that.
- **Milliseconds since the start of the session**, in a UINT32. This gives the
  same precision but repeats information `timestamp` already carries, and it
  needs the reader to find the start time first.

## Implementation

- Python: to follow in a companion pull request, writing and reading field 97
  and round-tripping it.
- Round-trip evidence: to be attached from that pull request.

## Open points

- Whether the field should also go on Lap and Session `start_time`. This
  proposal covers Record only, where the problem is.

## Discussion record

- Issue #69: the problem and the field were raised by the author.

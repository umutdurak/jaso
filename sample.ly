\version "2.22.2"

\header {
  title = "Sample Tune"
}

melody = \relative c' {
  \key c \major
  \time 4/4

  c4 d e f
  g a b c
}

mychords = \chordmode {
  c
  g
}

\score {
  <<
    \new ChordNames { \mychords }
    \new Staff { \melody }
  >>
}
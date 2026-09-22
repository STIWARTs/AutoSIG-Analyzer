# AutoSIG Analyzer — Project Overview

## Problem Statement

- **PS ID:** SIH26147
- **Title:** Automated model for analysis of .IQ and .wav files along with signal parameter extraction
- **Organization:** National Technical Research Organisation (NTRO)
- **Theme:** Space Technology
- **Category:** Software

## Team

- **Team ID:** 129944
- **Team Name:** TryCatchFinally
- **Product Name:** AutoSIG Analyzer

## Background

Signals collected off the air can range from a few kHz to the GHz bands, and today the analysis of these recordings is largely manual. An analyst has to inspect a raw `.IQ` or `.wav` recording and, mostly by eye and by hand, work out what the signal actually is: its modulation, its sampling rate, whether it has been interleaved, and what forward error correction (FEC) scheme protects it. This manual process does not scale, is inconsistent between analysts, and often cannot recover fine-grained parameters because the raw recordings themselves vary in quality and completeness depending on which sensor and location captured them.

## Problem Description

Terrestrial signals arrive in the HF, VHF, and UHF bands and are recorded as `.wav` or `.IQ` files to preserve their waveform characteristics. Because these recordings come from different sensors and different physical locations, their parameters are inconsistent — one recording might have a clean, well-characterized sample rate, while another is noisy or incomplete. This inconsistency makes it hard to reliably extract fine details such as sampling rate, modulation type, interleaving, and FEC, which in turn reduces the confidence of any downstream analysis. `.IQ` and `.wav` also store raw information in different underlying formats and therefore need different processing paths before they can be compared on equal footing. The problem statement calls for an advanced, GNU Radio/Python/C++-based model that can use the spectral relationships present in labeled training data (covering both `.IQ` and `.wav`) to identify signal parameters, carry out deeper analysis, and ultimately demodulate the signal.

## Required GUI Features (as specified by the PS)

The GUI-based model must accept a `.IQ` or `.wav` file as input and:

1. Identify signal parameters — sampling frequency, modulation, FEC, interleaving (and additional features where feasible).
2. Demodulate signals (FSK, QAM, PSK).
3. Carry out de-interleaving (Block, Convolutional, Diagonal, Pseudo-Random).
4. Perform FEC decoding (short-constraint convolutional codes with Viterbi decoding, Reed-Solomon block codes, concatenated codes, LDPC).
5. Perform bitstream correlation.

## Expected Solution

The system should improve the visibility of signal features through a GUI, automate the identification of spectral features (sampling frequency, constellation, waterfall/time-frequency view), demodulate the signal, de-interleave it, correct errors, and finally correlate the recovered bitstream to identify header and payload structure.

## What We Are Building — AutoSIG Analyzer

AutoSIG Analyzer is a hybrid DSP + AI/ML system that takes a `.IQ` or `.wav` recording and walks it through an automated pipeline: signal characterization, AI-assisted modulation identification, ranked hypothesis generation (modulation + interleaving + FEC combinations), an actual DSP recovery attempt for each hypothesis, and validation of that attempt through bitstream correlation against expected header/payload structure. Rather than trusting a single AI prediction, the system tests its top candidate configurations against real decoders and only accepts a result once it is backed by measurable evidence — a correlation score, not just a classifier's confidence.

The rest of this `docs/` folder specifies, in detail, every subsystem needed to build this as a working prototype, plus the visual design system for its interface. See `design.md` for the UI design specification.

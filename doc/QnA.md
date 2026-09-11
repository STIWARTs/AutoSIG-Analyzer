# 17. SIH Cross-Questions and Answers

## Q1. What exactly is DSP?

**Answer:** DSP is Digital Signal Processing. It is the mathematical processing of sampled signals, including filtering, FFT, spectrum analysis, synchronization, parameter estimation and demodulation.

## Q2. Why do you need AI if DSP already exists?

**Answer:** DSP is excellent for deterministic measurements, but some classification tasks are difficult to solve reliably using fixed thresholds. We use DSP to extract physically meaningful features and ML to rank likely modulation/FEC/interleaving candidates. The recovery engine then validates those candidates.

## Q3. Does AI directly decode the signal?

**Answer:** No. ML generates and ranks hypotheses. Actual demodulation, de-interleaving and FEC decoding are performed by signal-processing/decoder modules, followed by validation.

## Q4. Where does your labeled training data come from?

**Answer:** For supervised training, we generate controlled synthetic IQ datasets using GNU Radio with known ground-truth modulation, coding, interleaving and channel impairments. This lets us create labels automatically and vary SNR, frequency offset and timing offset.

## Q5. Why synthetic data?

**Answer:** Real unknown recordings generally do not contain reliable labels for every parameter. Synthetic data gives exact ground truth and lets us systematically cover controlled conditions. Real recordings can then be used for validation and later dataset improvement.

## Q6. Won't synthetic data differ from real signals?

**Answer:** Yes. That is a known limitation. We address it by varying channel impairments, validating on separate recordings where available, and treating the model as a candidate generator rather than the final authority. The recovery engine provides downstream validation.

## Q7. Why not test every combination?

**Answer:** The combination space can become computationally expensive. We use ML/DSP evidence to rank candidates and only test a configurable Top-K, such as three candidates. This bounds runtime.

## Q8. What happens if all candidates fail?

**Answer:** The system terminates after a configured retry limit and returns LOW CONFIDENCE or UNCLASSIFIED. It does not fabricate a successful interpretation.

## Q9. How do you know ML's prediction is correct?

**Answer:** We do not treat ML probability as proof. We verify the candidate through synchronization, demodulation, de-interleaving, FEC checks, correlation and frame consistency.

## Q10. How do DSP and ML predictions interact?

**Answer:** DSP provides physically grounded measurements such as symbol rate, bandwidth and SNR. ML provides classification probabilities. They are fused during candidate generation, and the recovery/validation stage determines whether a complete hypothesis works.

## Q11. Why is symbol rate not estimated twice?

**Answer:** DSP-based symbol-rate estimation is the primary estimator. ML can use it as a feature or cross-check, but we avoid maintaining two competing primary estimators.

## Q12. Can you determine sampling frequency from arbitrary IQ samples?

**Answer:** Not always. A raw IQ sequence without metadata does not inherently contain an absolute time scale. The system uses available metadata first and applies estimation only where there is sufficient information or a constrained assumption. Otherwise it reports the sample rate as unknown.

## Q13. What is a waterfall?

**Answer:** A waterfall is a time-frequency visualization, usually produced from consecutive FFT/STFT windows. It shows how spectral energy changes over time.

## Q14. What is a constellation plot?

**Answer:** It plots recovered complex symbols in the I/Q plane. Clusters can reveal modulation structures such as PSK and QAM, especially after synchronization.

## Q15. Why is synchronization necessary?

**Answer:** Frequency, phase and timing offsets can rotate or smear constellation points and cause incorrect symbol decisions. Synchronization aligns the received signal with the assumed symbol timing and carrier.

## Q16. What is FEC?

**Answer:** Forward Error Correction adds structured redundancy so a receiver can detect and correct some transmission errors.

## Q17. Why de-interleave before FEC?

**Answer:** Many systems intentionally rearrange coded bits so burst errors are distributed across the codeword. The receiver reverses that permutation before applying the corresponding FEC decoder when the signal chain specifies that order.

## Q18. What is Viterbi decoding?

**Answer:** Viterbi is a maximum-likelihood sequence decoding algorithm commonly used for convolutional codes. It searches efficiently through the code trellis for the most likely transmitted sequence.

## Q19. Why use soft bits?

**Answer:** Soft bits preserve reliability information rather than reducing every observation immediately to 0 or 1. FEC decoders can use that extra information to improve correction performance.

## Q20. What proves an FEC hypothesis is correct?

**Answer:** A decoder producing output is not enough. We combine decoder metrics with CRC/parity/syndrome checks, known-sequence correlation and frame consistency.

## Q21. What if the signal has multiple signals in one recording?

**Answer:** Signal detection and segmentation identifies active regions before detailed analysis. Each candidate segment can then be analyzed independently.

## Q22. What if the input is corrupted?

**Answer:** The input-validation layer detects malformed or unsupported files and returns an explicit error instead of sending invalid data into the DSP pipeline.

## Q23. Why support both IQ and WAV?

**Answer:** They are common ways of preserving sampled signal information, but they have different representation and metadata characteristics. A unified internal complex-sample representation allows the downstream DSP to operate consistently.

## Q24. Is WAV always an IQ file?

**Answer:** No. WAV is a container. It can hold real samples or, depending on the acquisition/export convention, multiple channels that may represent I/Q. The parser inspects the actual format.

## Q25. Why C# and Python?

**Answer:** C#/.NET is suitable for a polished desktop GUI, while Python has a mature scientific, DSP and ML ecosystem. The GUI communicates with the analysis engine through a defined interface.

## Q26. Why GNU Radio?

**Answer:** GNU Radio provides a practical environment for signal generation and SDR/DSP prototyping. It is especially useful for creating controlled synthetic training data with known ground truth.

## Q27. Why not use only GNU Radio?

**Answer:** GNU Radio is excellent for signal processing and flowgraph-based development, but our project also requires ML inference, hypothesis orchestration, reporting and a custom desktop workflow. We therefore use it as a component rather than forcing the entire application into one framework.

## Q28. Are CNN/ResNet/LSTM all required?

**Answer:** No. They are possible model families, not mandatory components. We begin with a baseline model and add complexity only when measured results justify it.

## Q29. Is GPU required?

**Answer:** No. GPU acceleration is optional. For the SIH demo, models should be pre-trained and inference should be benchmarked on the actual demo machine. We do not depend on training a large model during the live demonstration.

## Q30. What is your main innovation?

**Answer:** The innovation is the integration of automated DSP analysis, ML-assisted candidate generation and bounded hypothesis-based signal recovery into one workflow, with validation and confidence rather than a single unverified classifier output.

## Q31. What is the biggest technical risk?

**Answer:** Generalization from synthetic training data to real recordings and the complexity of reliable FEC/interleaving identification. We mitigate this by narrowing the MVP, generating controlled data, using known-ground-truth tests and treating ML as candidate generation rather than proof.

## Q32. Why not implement everything in the PS?

**Answer:** The architecture supports the full requirement set, but engineering priorities require a validated vertical slice first. We demonstrate a complete supported configuration and then expand modularly.

## Q33. What happens when the signal is unsupported?

**Answer:** The system returns an explicit unsupported/low-confidence state with evidence and processing logs.

## Q34. Can the system guarantee correct payload identification?

**Answer:** No. Header/payload boundaries are reliable when the protocol/frame structure is known or strongly evidenced. For unknown formats, the system reports candidate boundaries with confidence rather than claiming certainty.

## Q35. Does the system perform decryption?

**Answer:** No. Decryption is outside the stated scope. The system focuses on signal analysis, demodulation, de-interleaving, FEC recovery, bit correlation and header/payload identification.

## Q36. How do you prevent infinite recovery loops?

**Answer:** Candidate count, retry count and time per hypothesis are bounded configuration parameters. Every analysis has a terminal state.

## Q37. How will you measure success?

**Answer:** We measure parameter-estimation error, ML classification metrics, BER/FER on known-ground-truth data, decoder validation rate, false-success rate, runtime and memory.

## Q38. What makes your system auditable?

**Answer:** Every analysis records input metadata, configuration, model version, candidate hypotheses, algorithm results, validation metrics, warnings and timestamps. The final report includes the evidence behind the selected result.

## Q39. What is your first working milestone?

**Answer:** A QPSK end-to-end path with synchronization, demodulation, one de-interleaving scheme, convolutional FEC/Viterbi, known-sequence/CRC validation and report generation.

## Q40. What is the long-term architecture?

**Answer:** A modular signal-analysis framework where new modulation, FEC, interleaving and feature models can be added without redesigning the GUI or orchestration layer.

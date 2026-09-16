import csv
import json
import os
import sys
from datetime import datetime

import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QLabel,
    QPushButton,
    QToolButton,
    QFileDialog,
    QComboBox,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QStackedWidget,
    QProgressBar,
    QLineEdit,
    QTabWidget,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QAbstractItemView,
)


from src.app_controller import AnalysisController


# ================================================================
# COLOR SYSTEM
# ================================================================

ORANGE = "#F97316"
ORANGE_DARK = "#EA580C"
ORANGE_SOFT = "#FFF7ED"

NAVY = "#172554"
CHARCOAL = "#111827"
TEXT = "#1F2937"
MUTED = "#64748B"

BG = "#F7F8FA"
WHITE = "#FFFFFF"
BORDER = "#E5E7EB"

BLUE = "#2563EB"
GREEN = "#16A34A"
RED = "#DC2626"
GRAY = "#94A3B8"


# ================================================================
# PYQTGRAPH CONFIGURATION
# ================================================================

pg.setConfigOptions(
    background=WHITE,
    foreground=TEXT,
    antialias=True
)


# ================================================================
# COMMON PANEL
# ================================================================

class Panel(QFrame):

    def __init__(
        self,
        title=None,
        subtitle=None,
        parent=None
    ):
        super().__init__(parent)

        self.setObjectName("Panel")

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(
            16,
            14,
            16,
            16
        )

        self.layout.setSpacing(10)

        if title:

            head = QHBoxLayout()

            title_label = QLabel(
                title.upper()
            )

            title_label.setObjectName(
                "PanelTitle"
            )

            head.addWidget(title_label)

            head.addStretch()

            if subtitle:

                sub = QLabel(subtitle)

                sub.setObjectName(
                    "PanelMeta"
                )

                head.addWidget(sub)

            self.layout.addLayout(head)


# ================================================================
# METRIC CARD
# ================================================================

class MetricCard(Panel):

    def __init__(
        self,
        title,
        value="—",
        status="IDLE",
        accent=ORANGE
    ):

        super().__init__()

        self.title = QLabel(
            title.upper()
        )

        self.title.setObjectName(
            "MetricTitle"
        )

        self.value = QLabel(
            value
        )

        self.value.setObjectName(
            "MetricValue"
        )

        self.status = QLabel(
            status
        )

        self.status.setObjectName(
            "MetricStatus"
        )

        self.status.setStyleSheet(
            f"color:{accent};"
        )

        self.layout.addWidget(
            self.title
        )

        self.layout.addWidget(
            self.value
        )

        self.layout.addWidget(
            self.status
        )

    def set_value(
        self,
        value,
        status="READY",
        accent=ORANGE
    ):

        self.value.setText(
            str(value)
        )

        self.status.setText(
            status
        )

        self.status.setStyleSheet(
            f"color:{accent};"
        )


# ================================================================
# PLOT PANEL
# ================================================================

class PlotPanel(Panel):

    def __init__(
        self,
        title,
        parent=None
    ):

        super().__init__(
            title,
            parent=parent
        )

        self.plot = pg.PlotWidget()

        self.plot.showGrid(
            x=True,
            y=True,
            alpha=0.12
        )

        self.plot.getPlotItem().setMenuEnabled(
            False
        )

        self.plot.getPlotItem().hideButtons()

        self.layout.addWidget(
            self.plot,
            1
        )


# ================================================================
# BASE PAGE
# ================================================================

class PageBase(QWidget):

    def __init__(
        self,
        title,
        subtitle,
        controller,
        main_window
    ):

        super().__init__()

        self.controller = controller
        self.main_window = main_window

        root = QVBoxLayout(self)

        root.setContentsMargins(
            24,
            20,
            24,
            24
        )

        root.setSpacing(14)

        title_row = QHBoxLayout()

        title_box = QVBoxLayout()

        self.page_title = QLabel(
            title
        )

        self.page_title.setObjectName(
            "PageTitle"
        )

        self.page_subtitle = QLabel(
            subtitle
        )

        self.page_subtitle.setObjectName(
            "PageSubtitle"
        )

        title_box.addWidget(
            self.page_title
        )

        title_box.addWidget(
            self.page_subtitle
        )

        title_row.addLayout(
            title_box
        )

        title_row.addStretch()

        self.file_pill = QLabel(
            "NO SIGNAL LOADED"
        )

        self.file_pill.setObjectName(
            "SignalPill"
        )

        title_row.addWidget(
            self.file_pill,
            alignment=Qt.AlignTop
        )

        root.addLayout(
            title_row
        )

        self.content = QVBoxLayout()

        self.content.setSpacing(
            14
        )

        root.addLayout(
            self.content,
            1
        )

        self.root = root

    def update_file(self):

        meta = self.controller.metadata()

        if meta:
            self.file_pill.setText(
                meta["file_name"]
            )
        else:
            self.file_pill.setText(
                "NO SIGNAL LOADED"
            )


# ================================================================
# DASHBOARD
# ================================================================

class DashboardPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Signal Intelligence Dashboard",
            "Operational overview of the active RF recording",
            controller,
            main_window
        )

        # ============================================================
        # INPUT SIGNAL
        # ============================================================

        input_panel = Panel(
            "Input Signal",
            "Primary acquisition point"
        )

        input_panel.setObjectName(
            "DashboardInput"
        )

        input_grid = QGridLayout()

        input_grid.setHorizontalSpacing(
            18
        )

        input_grid.setVerticalSpacing(
            10
        )

        # ------------------------------------------------------------
        # ACQUISITION AREA
        # ------------------------------------------------------------

        drop = QFrame()

        drop.setObjectName(
            "DashboardDropZone"
        )

        dl = QVBoxLayout(drop)

        dl.setContentsMargins(
            20,
            16,
            20,
            16
        )

        dl.setSpacing(5)

        acquisition_label = QLabel(
            "ACTIVE ACQUISITION"
        )

        acquisition_label.setObjectName(
            "AcquisitionLabel"
        )

        self.drop_text = QLabel(
            "Drag & drop a signal file here"
        )

        self.drop_text.setObjectName(
            "DropTitle"
        )

        self.drop_meta = QLabel(
            "Supported formats  ·  IQ  ·  WAV  ·  DAT"
        )

        self.drop_meta.setObjectName(
            "PanelMeta"
        )

        dl.addWidget(
            acquisition_label
        )

        dl.addWidget(
            self.drop_text
        )

        dl.addWidget(
            self.drop_meta
        )

        input_grid.addWidget(
            drop,
            0,
            0,
            3,
            2
        )

        # ------------------------------------------------------------
        # METADATA
        # ------------------------------------------------------------

        metadata_frame = QFrame()

        metadata_frame.setObjectName(
            "MetadataFrame"
        )

        metadata_grid = QGridLayout(
            metadata_frame
        )

        metadata_grid.setContentsMargins(
            8,
            2,
            8,
            2
        )

        metadata_grid.setHorizontalSpacing(
            16
        )

        metadata_grid.setVerticalSpacing(
            6
        )

        self.meta_labels = {}

        fields = [
            ("File Name", "file_name"),
            ("Type", "file_type"),
            ("Size", "file_size"),
            ("Sampling Rate", "sampling_rate_text"),
            ("Duration", "duration_text"),
            ("Channel", "channel"),
        ]

        for row, (name, key) in enumerate(fields):

            key_label = QLabel(
                name.upper()
            )

            key_label.setObjectName(
                "TinyLabel"
            )

            value_label = QLabel(
                "—"
            )

            value_label.setObjectName(
                "TechValue"
            )

            self.meta_labels[key] = value_label

            metadata_grid.addWidget(
                key_label,
                row,
                0
            )

            metadata_grid.addWidget(
                value_label,
                row,
                1
            )

        input_grid.addWidget(
            metadata_frame,
            0,
            2,
            3,
            2
        )

        input_panel.layout.addLayout(
            input_grid
        )

        # ------------------------------------------------------------
        # INPUT CONTROLS
        # ------------------------------------------------------------

        controls = QHBoxLayout()

        controls.setSpacing(
            8
        )

        format_label = QLabel(
            "IQ FORMAT"
        )

        format_label.setObjectName(
            "TinyLabel"
        )

        self.format_combo = QComboBox()

        self.format_combo.addItems(
            [
                "complex64",
                "complex128",
                "int16",
                "float32"
            ]
        )

        self.format_combo.setFixedWidth(
            120
        )

        controls.addWidget(
            format_label
        )

        controls.addWidget(
            self.format_combo
        )

        controls.addStretch()

        self.open_btn = QPushButton(
            "OPEN FILE"
        )

        self.open_btn.setObjectName(
            "SecondaryButton"
        )

        self.open_btn.clicked.connect(
            main_window.open_file_dialog
        )

        self.analyze_btn = QPushButton(
            "ANALYZE SIGNAL  →"
        )

        self.analyze_btn.setObjectName(
            "PrimaryAnalyzeButton"
        )

        self.analyze_btn.clicked.connect(
            main_window.analyze_current
        )

        controls.addWidget(
            self.open_btn
        )

        controls.addWidget(
            self.analyze_btn
        )

        input_panel.layout.addLayout(
            controls
        )

        self.content.addWidget(
            input_panel
        )

        # ============================================================
        # ENGINEERING METRICS
        # ============================================================

        metrics = QGridLayout()

        metrics.setHorizontalSpacing(
            10
        )

        metrics.setVerticalSpacing(
            10
        )

        self.status_card = MetricCard(
            "Signal Status",
            "READY",
            "AWAITING ANALYSIS",
            GRAY
        )

        self.snr_card = MetricCard(
            "SNR",
            "—",
            "WAITING",
            GRAY
        )

        self.bw_card = MetricCard(
            "Estimated Bandwidth",
            "—",
            "WAITING",
            GRAY
        )

        self.mod_card = MetricCard(
            "Modulation Result",
            "—",
            "WAITING",
            GRAY
        )

        self.conf_card = MetricCard(
            "Confidence",
            "—",
            "WAITING",
            GRAY
        )

        self.baud_card = MetricCard(
            "Symbol Rate",
            "—",
            "WAITING",
            GRAY
        )

        cards = [
            self.status_card,
            self.snr_card,
            self.bw_card,
            self.mod_card,
            self.conf_card,
            self.baud_card
        ]

        for card in cards:
            card.setMinimumHeight(
                92
            )

        metrics.addWidget(
            self.status_card,
            0,
            0
        )

        metrics.addWidget(
            self.snr_card,
            0,
            1
        )

        metrics.addWidget(
            self.bw_card,
            0,
            2
        )

        metrics.addWidget(
            self.mod_card,
            0,
            3
        )

        metrics.addWidget(
            self.conf_card,
            0,
            4
        )

        metrics.addWidget(
            self.baud_card,
            0,
            5
        )

        self.content.addLayout(
            metrics
        )

        # ============================================================
        # VISUALIZATION AREA
        # ============================================================

        visual_grid = QGridLayout()

        visual_grid.setHorizontalSpacing(
            12
        )

        visual_grid.setVerticalSpacing(
            12
        )

        # ------------------------------------------------------------
        # SPECTRUM
        # ------------------------------------------------------------

        self.spectrum = PlotPanel(
            "Spectrum Overview"
        )

        self.spectrum.setMinimumHeight(
            230
        )

        # ------------------------------------------------------------
        # SIGNAL SUMMARY
        # ------------------------------------------------------------

        self.summary = Panel(
            "Signal Summary",
            "Engineering readout"
        )

        self.summary_text = QPlainTextEdit()

        self.summary_text.setReadOnly(
            True
        )

        self.summary_text.setObjectName(
            "Terminal"
        )

        self.summary.layout.addWidget(
            self.summary_text
        )

        # ------------------------------------------------------------
        # WATERFALL
        # ------------------------------------------------------------

        self.waterfall = PlotPanel(
            "Waterfall Overview"
        )

        self.waterfall.setMinimumHeight(
            210
        )

        # ------------------------------------------------------------
        # CONSTELLATION
        # ------------------------------------------------------------

        self.constellation = PlotPanel(
            "Constellation Overview"
        )

        self.constellation.setMinimumHeight(
            210
        )

        # ------------------------------------------------------------
        # GRID
        # ------------------------------------------------------------

        visual_grid.addWidget(
            self.spectrum,
            0,
            0,
            1,
            2
        )

        visual_grid.addWidget(
            self.summary,
            0,
            2,
            1,
            1
        )

        visual_grid.addWidget(
            self.waterfall,
            1,
            0,
            1,
            2
        )

        visual_grid.addWidget(
            self.constellation,
            1,
            2,
            1,
            1
        )

        self.content.addLayout(
            visual_grid,
            1
        )

        # ============================================================
        # PIPELINE FOOTER
        # ============================================================

        footer = QFrame()

        footer.setObjectName(
            "DashboardFooter"
        )

        footer_layout = QHBoxLayout(
            footer
        )

        footer_layout.setContentsMargins(
            12,
            8,
            12,
            8
        )

        self.workflow_state = QLabel(
            "PIPELINE  ·  INPUT → DSP → PARAMETERS → "
            "MODULATION → DEMODULATION"
        )

        self.workflow_state.setObjectName(
            "WorkflowStatus"
        )

        self.validation_state = QLabel(
            "VALIDATION  ·  STANDBY"
        )

        self.validation_state.setObjectName(
            "ValidationStatus"
        )

        footer_layout.addWidget(
            self.workflow_state
        )

        footer_layout.addStretch()

        footer_layout.addWidget(
            self.validation_state
        )

        self.content.addWidget(
            footer
        )

    # ================================================================
    # UPDATE DASHBOARD
    # ================================================================

    def update_from_results(self):

        self.update_file()

        meta = self.controller.metadata()

        if meta:

            for key, label in self.meta_labels.items():

                label.setText(
                    str(
                        meta.get(
                            key,
                            "—"
                        )
                    )
                )

        r = self.controller.results

        # ------------------------------------------------------------
        # NO ANALYSIS
        # ------------------------------------------------------------

        if not r:

            self.status_card.set_value(
                "READY",
                "AWAITING ANALYSIS",
                GRAY
            )

            self.snr_card.set_value(
                "—",
                "WAITING",
                GRAY
            )

            self.bw_card.set_value(
                "—",
                "WAITING",
                GRAY
            )

            self.mod_card.set_value(
                "—",
                "WAITING",
                GRAY
            )

            self.conf_card.set_value(
                "—",
                "WAITING",
                GRAY
            )

            self.baud_card.set_value(
                "—",
                "WAITING",
                GRAY
            )

            return

        # ------------------------------------------------------------
        # SIGNAL STATUS
        # ------------------------------------------------------------

        self.status_card.set_value(
            "ANALYZED",
            "DSP ONLINE",
            GREEN
        )

        # ------------------------------------------------------------
        # SNR
        # ------------------------------------------------------------

        self.snr_card.set_value(
            f"{r['snr']:.2f} dB",
            "MEASURED",
            ORANGE
        )

        # ------------------------------------------------------------
        # BANDWIDTH
        # ------------------------------------------------------------

        self.bw_card.set_value(
            f"{r['bandwidth'] / 1e3:.2f} kHz",
            "ESTIMATED",
            ORANGE
        )

        # ------------------------------------------------------------
        # MODULATION
        # ------------------------------------------------------------

        modulation = r.get(
            "modulation",
            "UNKNOWN"
        )

        preamble_confidence = r.get(
            "preamble_confidence",
            0.0
        )

        synthetic = r.get(
            "synthetic",
            False
        )

        if (
            preamble_confidence >= 0.80
            and not synthetic
        ):

            modulation_status = "VALIDATED"

            modulation_accent = GREEN

        else:

            modulation_status = (
                "HYPOTHESIS / HEURISTIC"
            )

            modulation_accent = ORANGE

        self.mod_card.set_value(
            modulation,
            modulation_status,
            modulation_accent
        )

        # ------------------------------------------------------------
        # CONFIDENCE
        # ------------------------------------------------------------

        self.conf_card.set_value(
            f"{r['confidence'] * 100:.1f}%",
            "COMPUTED SCORE",
            ORANGE
        )

        # ------------------------------------------------------------
        # SYMBOL RATE
        # ------------------------------------------------------------

        self.baud_card.set_value(
            f"{r['baud'] / 1e3:.2f} kBd",
            "ESTIMATED",
            ORANGE
        )

        # ============================================================
        # SIGNAL SUMMARY
        # ============================================================

        self.summary_text.setPlainText(

            f"ACTIVE FILE       "
            f"{meta.get('file_name', '—')}\n"

            f"SAMPLES           "
            f"{meta.get('samples', '—'):,}\n"

            f"SAMPLING RATE     "
            f"{meta.get('sampling_rate_text', '—')}\n"

            f"CENTER FREQUENCY  "
            f"{r['center_frequency'] / 1e3:.3f} kHz\n"

            f"PEAK FREQUENCY    "
            f"{r['peak_frequency'] / 1e3:.3f} kHz\n"

            f"PEAK POWER        "
            f"{r['peak_power']:.2f} dB\n"

            f"SNR               "
            f"{r['snr']:.2f} dB\n"

            f"MODULATION        "
            f"{modulation}\n"

            f"SYMBOL RATE       "
            f"{r['baud']:.2f} Baud\n"

            f"PREAMBLE          "
            f"{r['preamble_name'] or 'N/A'}\n"

            f"VALIDATION        "
            f"{r['validation']}"
        )

        # ============================================================
        # PIPELINE
        # ============================================================

        self.workflow_state.setText(
            "PIPELINE  ·  "
            "INPUT ✓  →  DSP ✓  →  PARAMETERS ✓  →  "
            "MODULATION ✓  →  DEMODULATION ✓"
        )

        validation = str(
            r.get(
                "validation",
                "STANDBY"
            )
        ).upper()

        self.validation_state.setText(
            f"VALIDATION  ·  {validation}"
        )

        if (
            "VALID" in validation
            or "PASS" in validation
        ):

            self.validation_state.setStyleSheet(
                f"color:{GREEN};"
            )

        else:

            self.validation_state.setStyleSheet(
                f"color:{ORANGE};"
            )

        # ============================================================
        # PLOTS
        # ============================================================

        self._plot_spectrum(
            self.spectrum.plot,
            r
        )

        self._plot_waterfall(
            self.waterfall.plot,
            r
        )

        self._plot_constellation(
            self.constellation.plot,
            r.get(
                "symbols",
                np.array([])
            )
        )

    # ================================================================
    # SPECTRUM PLOT
    # ================================================================

    def _plot_spectrum(
        self,
        plot,
        r
    ):

        plot.clear()

        freqs = (
            r["freqs"] / 1e3
        )

        psd = r["psd"]

        plot.plot(
            freqs,
            psd,
            pen=pg.mkPen(
                ORANGE,
                width=1.35
            )
        )

        peak_index = int(
            np.argmax(psd)
        )

        peak_x = freqs[
            peak_index
        ]

        peak_y = psd[
            peak_index
        ]

        plot.plot(
            [peak_x],
            [peak_y],
            pen=None,
            symbol="o",
            symbolSize=7,
            symbolBrush=QColor(
                ORANGE
            ),
            symbolPen=pg.mkPen(
                ORANGE_DARK,
                width=1
            )
        )

        plot.setLabel(
            "bottom",
            "Frequency",
            units="kHz"
        )

        plot.setLabel(
            "left",
            "Power",
            units="dB"
        )

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.10
        )

    # ================================================================
    # WATERFALL PLOT
    # ================================================================

    def _plot_waterfall(
        self,
        plot,
        r
    ):

        plot.clear()

        img = pg.ImageItem()

        img.setImage(
            r["spec_db"],
            autoLevels=True
        )

        f = (
            r["spec_f"] / 1e3
        )

        t = r["spec_t"]

        if (
            len(f) > 1
            and len(t) > 1
        ):

            img.setRect(
                QRectF(
                    float(t[0]),
                    float(f[0]),
                    float(t[-1] - t[0]),
                    float(f[-1] - f[0])
                )
            )

        plot.addItem(
            img
        )

        plot.setLabel(
            "bottom",
            "Time",
            units="s"
        )

        plot.setLabel(
            "left",
            "Frequency",
            units="kHz"
        )

        plot.showGrid(
            x=False,
            y=False
        )

    # ================================================================
    # CONSTELLATION PLOT
    # ================================================================

    def _plot_constellation(
        self,
        plot,
        symbols
    ):

        plot.clear()

        if symbols is None:
            return

        s = symbols[:2500]

        if len(s):

            plot.plot(
                np.real(s),
                np.imag(s),
                pen=None,
                symbol="o",
                symbolSize=4,
                symbolBrush=QColor(
                    ORANGE
                ),
                symbolPen=None
            )

        plot.setLabel(
            "bottom",
            "In-phase",
            units="I"
        )

        plot.setLabel(
            "left",
            "Quadrature",
            units="Q"
        )

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.10
        )


# ================================================================
# SPECTRUM PAGE
# ================================================================

class SpectrumPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Spectrum Analysis",
            "FFT-based RF spectral workspace",
            controller,
            main_window
        )

        controls = Panel(
            "Spectrum Controls"
        )

        row = QHBoxLayout()

        self.center = QDoubleSpinBox()
        self.center.setRange(
            -1e9,
            1e9
        )
        self.center.setSuffix(
            " Hz"
        )

        self.span = QDoubleSpinBox()
        self.span.setRange(
            1,
            1e9
        )
        self.span.setValue(
            1e6
        )
        self.span.setSuffix(
            " Hz"
        )

        self.rbw = QDoubleSpinBox()
        self.rbw.setRange(
            1,
            1e8
        )
        self.rbw.setValue(
            1000
        )
        self.rbw.setSuffix(
            " Hz"
        )

        self.window = QComboBox()

        self.window.addItems(
            [
                "Blackman",
                "Hann",
                "Hamming",
                "Rectangular"
            ]
        )

        for label, widget in [
            ("CENTER", self.center),
            ("SPAN", self.span),
            ("RBW", self.rbw),
            ("WINDOW", self.window)
        ]:

            box = QVBoxLayout()

            l = QLabel(
                label
            )

            l.setObjectName(
                "TinyLabel"
            )

            box.addWidget(
                l
            )

            box.addWidget(
                widget
            )

            row.addLayout(
                box
            )

        row.addStretch()

        controls.layout.addLayout(
            row
        )

        self.content.addWidget(
            controls
        )

        grid = QGridLayout()

        self.plot_panel = PlotPanel(
            "Spectrum Analysis"
        )

        self.measure = Panel(
            "Measurements"
        )

        self.measure_text = QPlainTextEdit()

        self.measure_text.setReadOnly(
            True
        )

        self.measure_text.setObjectName(
            "Terminal"
        )

        self.measure.layout.addWidget(
            self.measure_text
        )

        grid.addWidget(
            self.plot_panel,
            0,
            0,
            1,
            3
        )

        grid.addWidget(
            self.measure,
            1,
            0,
            1,
            3
        )

        self.content.addLayout(
            grid,
            1
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        self.center.setValue(
            r["center_frequency"]
        )

        self._plot(
            r
        )

        self.measure_text.setPlainText(

            f"CENTER FREQUENCY   "
            f"{r['center_frequency']:.3f} Hz\n"

            f"PEAK FREQUENCY      "
            f"{r['peak_frequency']:.3f} Hz\n"

            f"PEAK POWER          "
            f"{r['peak_power']:.2f} dB\n"

            f"BANDWIDTH (-3 dB)   "
            f"{r['bandwidth']:.3f} Hz\n"

            f"SNR                 "
            f"{r['snr']:.2f} dB\n"

            f"SYMBOL RATE         "
            f"{r['baud']:.2f} Baud"
        )

    def _plot(
        self,
        r
    ):

        p = self.plot_panel.plot

        p.clear()

        p.plot(
            r["freqs"] / 1e3,
            r["psd"],
            pen=pg.mkPen(
                ORANGE,
                width=1.2
            )
        )

        idx = int(
            np.argmax(
                r["psd"]
            )
        )

        p.plot(
            [
                r["freqs"][idx] / 1e3
            ],
            [
                r["psd"][idx]
            ],
            pen=None,
            symbol="o",
            symbolSize=9,
            symbolBrush=ORANGE
        )

        p.setLabel(
            "bottom",
            "Frequency",
            units="kHz"
        )

        p.setLabel(
            "left",
            "Power",
            units="dB"
        )


# ================================================================
# WATERFALL PAGE
# ================================================================

class WaterfallPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Waterfall Monitor",
            "Time-frequency occupancy and spectral persistence",
            controller,
            main_window
        )

        controls = Panel(
            "Waterfall Controls"
        )

        row = QHBoxLayout()

        for text in [
            "START",
            "END"
        ]:

            e = QDoubleSpinBox()

            e.setRange(
                -1e9,
                1e9
            )

            e.setSuffix(
                " Hz"
            )

            row.addWidget(
                QLabel(text)
            )

            row.addWidget(
                e
            )

        fft = QComboBox()

        fft.addItems(
            [
                "512",
                "1024",
                "2048",
                "4096",
                "8192"
            ]
        )

        overlap = QComboBox()

        overlap.addItems(
            [
                "25%",
                "50%",
                "75%"
            ]
        )

        overlap.setCurrentText(
            "50%"
        )

        row.addWidget(
            QLabel("FFT SIZE")
        )

        row.addWidget(
            fft
        )

        row.addWidget(
            QLabel("OVERLAP")
        )

        row.addWidget(
            overlap
        )

        row.addStretch()

        controls.layout.addLayout(
            row
        )

        self.content.addWidget(
            controls
        )

        self.plot_panel = PlotPanel(
            "Waterfall / Spectrogram"
        )

        self.content.addWidget(
            self.plot_panel,
            1
        )

        self.readout = QLabel(
            "Awaiting signal analysis"
        )

        self.readout.setObjectName(
            "TechnicalReadout"
        )

        self.content.addWidget(
            self.readout
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        p = self.plot_panel.plot

        p.clear()

        img = pg.ImageItem()

        img.setImage(
            r["spec_db"],
            autoLevels=True
        )

        f = r["spec_f"] / 1e3
        t = r["spec_t"]

        if (
            len(f) > 1
            and len(t) > 1
        ):

            img.setRect(
                QRectF(
                    float(t[0]),
                    float(f[0]),
                    float(t[-1] - t[0]),
                    float(f[-1] - f[0])
                )
            )

        p.addItem(
            img
        )

        p.setLabel(
            "bottom",
            "Time",
            units="s"
        )

        p.setLabel(
            "left",
            "Frequency",
            units="kHz"
        )

        self.readout.setText(
            f"TIME SPAN  {t[-1]:.3f} s"
            f"    ·    "
            f"FREQ SPAN  "
            f"{f[0]:.1f} → {f[-1]:.1f} kHz"
        )


# ================================================================
# CONSTELLATION PAGE
# ================================================================

class ConstellationPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Constellation Analysis",
            "Symbol-cluster inspection and modulation quality",
            controller,
            main_window
        )

        controls = Panel(
            "Constellation Controls"
        )

        row = QHBoxLayout()

        self.count = QSpinBox()

        self.count.setRange(
            100,
            20000
        )

        self.count.setValue(
            3000
        )

        self.freeze = QCheckBox(
            "Freeze"
        )

        self.auto = QCheckBox(
            "Auto Scale"
        )

        self.auto.setChecked(
            True
        )

        row.addWidget(
            QLabel("SYMBOLS")
        )

        row.addWidget(
            self.count
        )

        row.addWidget(
            self.freeze
        )

        row.addWidget(
            self.auto
        )

        clear = QPushButton(
            "CLEAR"
        )

        clear.setObjectName(
            "SecondaryButton"
        )

        clear.clicked.connect(
            lambda:
            self.plot_panel.plot.clear()
        )

        row.addWidget(
            clear
        )

        row.addStretch()

        controls.layout.addLayout(
            row
        )

        self.content.addWidget(
            controls
        )

        grid = QGridLayout()

        self.plot_panel = PlotPanel(
            "I/Q Constellation"
        )

        self.info = Panel(
            "Signal Quality"
        )

        self.info_text = QPlainTextEdit()

        self.info_text.setReadOnly(
            True
        )

        self.info_text.setObjectName(
            "Terminal"
        )

        self.info.layout.addWidget(
            self.info_text
        )

        grid.addWidget(
            self.plot_panel,
            0,
            0,
            1,
            2
        )

        grid.addWidget(
            self.info,
            1,
            0,
            1,
            2
        )

        self.content.addLayout(
            grid,
            1
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        p = self.plot_panel.plot

        p.clear()

        s = r["symbols"][
            :self.count.value()
        ]

        if len(s):

            p.plot(
                np.real(s),
                np.imag(s),
                pen=None,
                symbol="o",
                symbolSize=5,
                symbolBrush=QColor(
                    ORANGE
                )
            )

        p.setLabel(
            "bottom",
            "In-phase (I)"
        )

        p.setLabel(
            "left",
            "Quadrature (Q)"
        )

        evm = (
            "N/A"
            if r["evm"] is None
            else f"{r['evm']:.2f}%"
        )

        self.info_text.setPlainText(

            f"MODULATION       "
            f"{r['modulation']}\n"

            f"SYMBOL RATE      "
            f"{r['baud']:.2f} Baud\n"

            f"SNR              "
            f"{r['snr']:.2f} dB\n"

            f"EVM              "
            f"{evm}\n"

            f"FREQ OFFSET      "
            f"{r['frequency_offset']:.2f} Hz\n"

            f"CONFIDENCE       "
            f"{r['confidence'] * 100:.1f}%"
        )


# ================================================================
# PARAMETER ESTIMATION
# ================================================================

class ParametersPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Parameter Estimation",
            "Engineering measurements and validation state",
            controller,
            main_window
        )

        self.table = QTableWidget(
            0,
            4
        )

        self.table.setHorizontalHeaderLabels(
            [
                "PARAMETER",
                "ESTIMATED VALUE",
                "STATUS",
                "CONFIDENCE"
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.content.addWidget(
            self.table,
            1
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        candidates = r.get(
            "candidates",
            []
        )

        candidate_confidence = (
            candidates[0]["confidence"]
            if candidates
            else 0.0
        )

        rows = [

            (
                "Sampling Frequency",
                self.controller.metadata().get(
                    "sampling_rate_text",
                    "—"
                ),
                "Measured",
                "—"
            ),

            (
                "Center / Peak Frequency",
                f"{r['center_frequency']:.3f} Hz",
                "Estimated",
                "—"
            ),

            (
                "Bandwidth",
                f"{r['bandwidth']:.3f} Hz",
                "Estimated",
                "—"
            ),

            (
                "Symbol Rate",
                f"{r['baud']:.2f} Baud",
                "Estimated",
                "—"
            ),

            (
                "Modulation",
                r["modulation"],
                "Hypothesis",
                f"{candidate_confidence * 100:.1f}%"
            ),

            (
                "SNR",
                f"{r['snr']:.2f} dB",
                "Measured",
                "—"
            ),

            (
                "Frequency Offset",
                f"{r['frequency_offset']:.2f} Hz",
                "Estimated",
                "—"
            ),

            (
                "FEC",
                r["fec"],
                "Pipeline",
                "—"
            ),

            (
                "Interleaving",
                r["interleaving"],
                "Pipeline",
                "—"
            ),

            (
                "Preamble",
                r["preamble_name"] or "Not validated",
                "Validation",
                f"{r['preamble_confidence'] * 100:.1f}%"
            ),

            (
                "Overall Confidence",
                f"{r['confidence'] * 100:.1f}%",
                "Computed",
                "—"
            )
        ]

        self.table.setRowCount(
            len(rows)
        )

        for i, row in enumerate(rows):

            for j, value in enumerate(row):

                self.table.setItem(
                    i,
                    j,
                    QTableWidgetItem(
                        str(value)
                    )
                )


# ================================================================
# MODULATION CANDIDATES
# ================================================================

class CandidatesPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Modulation Candidates",
            "Hypothesis generation separated from downstream validation",
            controller,
            main_window
        )

        workflow = Panel(
            "Analysis Chain"
        )

        chain = QLabel(
            "RAW SIGNAL  →  FEATURES  →  "
            "ML / HEURISTIC HYPOTHESES  →  "
            "SYNCHRONIZATION  →  DEMODULATION  →  "
            "FEC  →  VALIDATION"
        )

        chain.setObjectName(
            "WorkflowLabel"
        )

        chain.setWordWrap(
            True
        )

        workflow.layout.addWidget(
            chain
        )

        self.content.addWidget(
            workflow
        )

        self.table = QTableWidget(
            0,
            4
        )

        self.table.setHorizontalHeaderLabels(
            [
                "CANDIDATE",
                "RELATIVE CONFIDENCE",
                "DISTANCE SCORE",
                "ROLE"
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.content.addWidget(
            self.table,
            1
        )

        note = QLabel(
            "Candidate confidence is derived from the current "
            "heuristic feature-distance model. "
            "No ML model is installed in this prototype."
        )

        note.setObjectName(
            "PanelMeta"
        )

        self.content.addWidget(
            note
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        candidates = r.get(
            "candidates",
            []
        )

        self.table.setRowCount(
            len(candidates)
        )

        for i, candidate in enumerate(
            candidates
        ):

            role = (
                "PRIMARY CANDIDATE"
                if i == 0
                else "ALTERNATIVE"
            )

            values = [

                candidate["name"],

                f"{candidate['confidence'] * 100:.2f}%",

                f"{candidate['score']:.6f}",

                role
            ]

            for j, value in enumerate(
                values
            ):

                self.table.setItem(
                    i,
                    j,
                    QTableWidgetItem(
                        str(value)
                    )
                )


# ================================================================
# DEMODULATION
# ================================================================

class DemodPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Demodulation",
            "Receiver-chain execution status and recovered symbol stream",
            controller,
            main_window
        )

        pipeline = Panel(
            "Demodulation Pipeline"
        )

        grid = QGridLayout()

        self.stage_labels = []

        stages = [

            "IQ Samples",

            "Timing / Symbol Sampling",

            "Frequency Correction",

            "Carrier Recovery",

            "Demodulation",

            "Recovered Symbols",

            "Recovered Bits"
        ]

        for i, stage in enumerate(
            stages
        ):

            frame = QFrame()

            frame.setObjectName(
                "StageBox"
            )

            layout = QVBoxLayout(
                frame
            )

            title = QLabel(
                stage
            )

            title.setObjectName(
                "TinyLabel"
            )

            status = QLabel(
                "IDLE"
            )

            status.setObjectName(
                "StageStatus"
            )

            layout.addWidget(
                title
            )

            layout.addWidget(
                status
            )

            self.stage_labels.append(
                status
            )

            grid.addWidget(
                frame,
                i // 4,
                i % 4
            )

        pipeline.layout.addLayout(
            grid
        )

        self.content.addWidget(
            pipeline
        )

        info = Panel(
            "Demodulation Measurements"
        )

        self.info = QPlainTextEdit()

        self.info.setReadOnly(
            True
        )

        self.info.setObjectName(
            "Terminal"
        )

        info.layout.addWidget(
            self.info
        )

        self.content.addWidget(
            info,
            1
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        for status in self.stage_labels:

            status.setText(
                "✓ COMPLETE"
            )

            status.setStyleSheet(
                f"color:{GREEN};"
            )

        evm = (
            "N/A"
            if r["evm"] is None
            else f"{r['evm']:.2f}%"
        )

        ber = (
            "N/A — no reference sequence"
            if r["ber"] is None
            else r["ber"]
        )

        self.info.setPlainText(

            f"INPUT SAMPLES     "
            f"{len(self.controller.signal_data):,}\n"

            f"OUTPUT SYMBOLS    "
            f"{len(r['symbols']):,}\n"

            f"RECOVERED BITS    "
            f"{len(r['bits']):,}\n"

            f"MODULATION        "
            f"{r['modulation']}\n"

            f"SNR               "
            f"{r['snr']:.2f} dB\n"

            f"EVM               "
            f"{evm}\n"

            f"BER               "
            f"{ber}\n"

            f"CONFIDENCE        "
            f"{r['confidence'] * 100:.1f}%"
        )


# ================================================================
# DECODED OUTPUT
# ================================================================

class OutputPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Decoded Output",
            "Frame, bitstream and payload inspection",
            controller,
            main_window
        )

        buttons = QHBoxLayout()

        actions = [

            (
                "SAVE BITSTREAM",
                lambda: self.export_bits()
            ),

            (
                "EXPORT HEX",
                lambda: self.export_hex()
            ),

            (
                "EXPORT ASCII",
                lambda: self.export_ascii()
            ),

            (
                "EXPORT JSON",
                lambda: main_window.export_json()
            )
        ]

        for text, slot in actions:

            button = QPushButton(
                text
            )

            button.setObjectName(
                "SecondaryButton"
            )

            button.clicked.connect(
                slot
            )

            buttons.addWidget(
                button
            )

        buttons.addStretch()

        self.content.addLayout(
            buttons
        )

        tabs = QTabWidget()

        self.bits = QPlainTextEdit()
        self.bits.setReadOnly(True)
        self.bits.setObjectName(
            "BitTerminal"
        )

        self.hex = QPlainTextEdit()
        self.hex.setReadOnly(True)
        self.hex.setObjectName(
            "BitTerminal"
        )

        self.ascii = QPlainTextEdit()
        self.ascii.setReadOnly(True)
        self.ascii.setObjectName(
            "BitTerminal"
        )

        self.frame = QPlainTextEdit()
        self.frame.setReadOnly(True)
        self.frame.setObjectName(
            "BitTerminal"
        )

        tabs.addTab(
            self.bits,
            "Bit Stream"
        )

        tabs.addTab(
            self.hex,
            "Hex"
        )

        tabs.addTab(
            self.ascii,
            "ASCII"
        )

        tabs.addTab(
            self.frame,
            "Frame"
        )

        self.content.addWidget(
            tabs,
            1
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        decoded_bits = r[
            "decoded_bits"
        ]

        bits = (
            decoded_bits
            if len(decoded_bits)
            else r["bits"]
        )

        bit_text = "".join(
            map(
                str,
                bits.tolist()
            )
        )

        self.bits.setPlainText(

            "\n".join(
                bit_text[i:i + 64]
                for i in range(
                    0,
                    len(bit_text),
                    64
                )
            )
            or
            "No decoded bits"
        )

        payload = (
            r["payload"]
            if len(r["payload"])
            else bits
        )

        padded = (

            np.pad(
                payload,
                (
                    0,
                    (-len(payload)) % 8
                )
            )

            if len(payload)

            else
            np.array(
                [],
                dtype=np.uint8
            )
        )

        hx = (

            " ".join(
                f"{b:02X}"
                for b in np.packbits(
                    padded
                )
            )

            if len(padded)

            else ""
        )

        self.hex.setPlainText(
            hx
            or
            "No byte-aligned output"
        )

        self.ascii.setPlainText(
            self._ascii(payload)
            or
            "No printable payload"
        )

        self.frame.setPlainText(

            f"PREAMBLE\n"
            f"{r['preamble_name'] or 'N/A'}\n\n"

            f"INDEX\n"
            f"{r['preamble_index']}\n\n"

            f"CONFIDENCE\n"
            f"{r['preamble_confidence'] * 100:.2f}%\n\n"

            f"PAYLOAD\n"
            f"{''.join(map(str, r['payload'])) if len(r['payload']) else 'N/A'}\n\n"

            f"CRC / PARITY\n"
            f"Not implemented for unknown protocol"
        )

    @staticmethod
    def _ascii(bits):

        if len(bits) == 0:
            return ""

        bits = np.pad(
            bits,
            (
                0,
                (-len(bits)) % 8
            )
        )

        raw = np.packbits(
            bits
        ).tobytes()

        return "".join(
            chr(x)
            if 32 <= x <= 126
            else "."
            for x in raw
        )

    def export_bits(self):

        r = self.controller.results

        if not r:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Bitstream",
            "decoded_bits.txt",
            "Text (*.txt)"
        )

        if path:

            bits = (
                r["decoded_bits"]
                if len(r["decoded_bits"])
                else r["bits"]
            )

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    "".join(
                        map(
                            str,
                            bits.tolist()
                        )
                    )
                )

    def export_hex(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export HEX",
            "decoded.hex",
            "HEX (*.hex)"
        )

        if path:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    self.hex.toPlainText()
                )

    def export_ascii(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export ASCII",
            "decoded.txt",
            "Text (*.txt)"
        )

        if path:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(
                    self.ascii.toPlainText()
                )


# ================================================================
# FILE MANAGER
# ================================================================

class FilesPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "File Manager",
            "Signal acquisition and local recording inventory",
            controller,
            main_window
        )

        actions = QHBoxLayout()

        import_button = QPushButton(
            "IMPORT"
        )

        import_button.clicked.connect(
            main_window.open_file_dialog
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setObjectName(
            "SecondaryButton"
        )

        refresh_button.clicked.connect(
            self.refresh
        )

        actions.addWidget(
            import_button
        )

        actions.addWidget(
            refresh_button
        )

        actions.addStretch()

        self.content.addLayout(
            actions
        )

        self.table = QTableWidget(
            0,
            7
        )

        self.table.setHorizontalHeaderLabels(
            [
                "FILE NAME",
                "TYPE",
                "SIZE",
                "SAMPLES",
                "SAMPLING RATE",
                "DURATION",
                "STATUS"
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.content.addWidget(
            self.table,
            1
        )

    def refresh(self):

        root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "data"
            )
        )

        rows = []

        if os.path.isdir(root):

            for name in sorted(
                os.listdir(root)
            ):

                path = os.path.join(
                    root,
                    name
                )

                if (
                    os.path.isfile(path)
                    and
                    os.path.splitext(
                        name
                    )[1].lower()
                    in (
                        ".iq",
                        ".wav",
                        ".dat"
                    )
                ):

                    rows.append(
                        path
                    )

        if (
            self.controller.file_path
            and
            self.controller.file_path
            not in rows
        ):

            rows.append(
                self.controller.file_path
            )

        self.table.setRowCount(
            len(rows)
        )

        for i, path in enumerate(
            rows
        ):

            size = os.path.getsize(
                path
            )

            active = (
                os.path.abspath(path)
                ==
                os.path.abspath(
                    self.controller.file_path
                    or ""
                )
            )

            values = [

                os.path.basename(
                    path
                ),

                os.path.splitext(
                    path
                )[1].upper().replace(
                    ".",
                    ""
                ),

                AnalysisController._format_bytes(
                    size
                ),

                "—",

                "—",

                "—",

                "ACTIVE"
                if active
                else
                "READY"
            ]

            for j, value in enumerate(
                values
            ):

                self.table.setItem(
                    i,
                    j,
                    QTableWidgetItem(
                        str(value)
                    )
                )


# ================================================================
# REPORTS
# ================================================================

class ReportsPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Reports",
            "Engineering analysis report generation",
            controller,
            main_window
        )

        actions = QHBoxLayout()

        report_actions = [

            (
                "GENERATE PDF",
                main_window.export_pdf
            ),

            (
                "EXPORT JSON",
                main_window.export_json
            ),

            (
                "EXPORT CSV",
                self.export_csv
            )
        ]

        for text, slot in report_actions:

            button = QPushButton(
                text
            )

            button.clicked.connect(
                slot
            )

            actions.addWidget(
                button
            )

        actions.addStretch()

        self.content.addLayout(
            actions
        )

        self.preview = QPlainTextEdit()

        self.preview.setReadOnly(
            True
        )

        self.preview.setObjectName(
            "BitTerminal"
        )

        self.content.addWidget(
            self.preview,
            1
        )

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        m = self.controller.metadata()

        lines = [

            "SIGNAL INTELLIGENCE ANALYSIS REPORT",

            "=" * 64,

            f"Generated: "
            f"{datetime.now():%Y-%m-%d %H:%M:%S}",

            f"File: "
            f"{m.get('file_name', '—')}",

            "",

            "SIGNAL SUMMARY",

            "-" * 64,

            f"Samples: "
            f"{m.get('samples', '—'):,}",

            f"Sampling rate: "
            f"{m.get('sampling_rate_text', '—')}",

            f"Duration: "
            f"{m.get('duration_text', '—')}",

            f"SNR: "
            f"{r['snr']:.2f} dB",

            f"Bandwidth: "
            f"{r['bandwidth']:.3f} Hz",

            f"Peak frequency: "
            f"{r['peak_frequency']:.3f} Hz",

            f"Symbol rate: "
            f"{r['baud']:.2f} Baud",

            f"Modulation candidate: "
            f"{r['modulation']}",

            f"Confidence: "
            f"{r['confidence'] * 100:.2f}%",

            "",

            "VALIDATION",

            "-" * 64,

            f"Preamble: "
            f"{r['preamble_name'] or 'N/A'}",

            f"Preamble confidence: "
            f"{r['preamble_confidence'] * 100:.2f}%",

            f"FEC: "
            f"{r['fec']}",

            f"Interleaving: "
            f"{r['interleaving']}",

            f"Frame status: "
            f"{r['validation']}"
        ]

        self.preview.setPlainText(
            "\n".join(lines)
        )

    def export_csv(self):

        if not self.controller.results:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "signal_report.csv",
            "CSV (*.csv)"
        )

        if not path:
            return

        r = self.controller.results

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(
                f
            )

            writer.writerow(
                [
                    "Parameter",
                    "Value"
                ]
            )

            for key in [

                "power",
                "rms",
                "snr",
                "baud",
                "peak_frequency",
                "peak_power",
                "bandwidth",
                "modulation",
                "confidence",
                "preamble_name",
                "preamble_index",
                "preamble_confidence",
                "fec",
                "interleaving",
                "validation"

            ]:

                writer.writerow(
                    [
                        key,
                        r.get(key)
                    ]
                )


# ================================================================
# SETTINGS
# ================================================================

class SettingsPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Settings",
            "Display, DSP and application configuration",
            controller,
            main_window
        )

        grid = QGridLayout()

        self.fft = QComboBox()

        self.fft.addItems(
            [
                "1024",
                "2048",
                "4096",
                "8192",
                "16384"
            ]
        )

        self.fft.setCurrentText(
            "8192"
        )

        self.window = QComboBox()

        self.window.addItems(
            [
                "Blackman",
                "Hann",
                "Hamming",
                "Rectangular"
            ]
        )

        self.window.setCurrentText(
            "Blackman"
        )

        gpu = QCheckBox(
            "GPU Acceleration"
        )

        gpu.setChecked(
            False
        )

        autosave = QCheckBox(
            "Auto Save Reports"
        )

        autosave.setChecked(
            True
        )

        theme = QComboBox()

        theme.addItems(
            [
                "Light",
                "System"
            ]
        )

        values = [

            (
                "FFT Size",
                self.fft
            ),

            (
                "Window",
                self.window
            ),

            (
                "",
                gpu
            ),

            (
                "",
                autosave
            ),

            (
                "Theme",
                theme
            )
        ]

        for i, (label, widget) in enumerate(
            values
        ):

            grid.addWidget(
                QLabel(
                    label.upper()
                ),
                i,
                0
            )

            grid.addWidget(
                widget,
                i,
                1
            )

        panel = Panel(
            "Application Configuration"
        )

        panel.layout.addLayout(
            grid
        )

        self.content.addWidget(
            panel
        )

        self.content.addStretch()


# ================================================================
# SIGNAL ANALYSIS PAGE
# ================================================================

class AnalysisPage(PageBase):

    def __init__(
        self,
        controller,
        main_window
    ):

        super().__init__(
            "Signal Analysis",
            "Core preprocessing, measurements and analysis diagnostics",
            controller,
            main_window
        )

        self.content.addWidget(
            self._build()
        )

    def _build(self):

        wrapper = QWidget()

        grid = QGridLayout(
            wrapper
        )

        self.power = MetricCard(
            "Average Power"
        )

        self.rms = MetricCard(
            "RMS"
        )

        self.snr = MetricCard(
            "SNR"
        )

        self.baud = MetricCard(
            "Symbol Rate"
        )

        cards = [
            self.power,
            self.rms,
            self.snr,
            self.baud
        ]

        for i, card in enumerate(
            cards
        ):

            grid.addWidget(
                card,
                0,
                i
            )

        diagnostics = Panel(
            "Analysis Diagnostics"
        )

        self.text = QPlainTextEdit()

        self.text.setReadOnly(
            True
        )

        self.text.setObjectName(
            "Terminal"
        )

        diagnostics.layout.addWidget(
            self.text
        )

        grid.addWidget(
            diagnostics,
            1,
            0,
            1,
            4
        )

        return wrapper

    def update_from_results(self):

        self.update_file()

        r = self.controller.results

        if not r:
            return

        self.power.set_value(
            f"{r['power']:.6f}",
            "MEASURED",
            ORANGE
        )

        self.rms.set_value(
            f"{r['rms']:.6f}",
            "MEASURED",
            ORANGE
        )

        self.snr.set_value(
            f"{r['snr']:.2f} dB",
            "MEASURED",
            ORANGE
        )

        self.baud.set_value(
            f"{r['baud']:.2f} Baud",
            "ESTIMATED",
            ORANGE
        )

        self.text.setPlainText(

            f"FFT bins             "
            f"{len(r['freqs']):,}\n"

            f"Spectrogram bins     "
            f"{r['spec_db'].shape[0]} × "
            f"{r['spec_db'].shape[1]}\n"

            f"Peak frequency       "
            f"{r['peak_frequency']:.3f} Hz\n"

            f"Peak power           "
            f"{r['peak_power']:.2f} dB\n"

            f"Bandwidth (-3 dB)    "
            f"{r['bandwidth']:.3f} Hz\n"

            f"Detected candidate   "
            f"{r['modulation']}\n"

            f"Recovered symbols    "
            f"{len(r['symbols']):,}\n"

            f"Recovered bits       "
            f"{len(r['bits']):,}\n"

            f"Validation           "
            f"{r['validation']}"
        )


# ================================================================
# MAIN WINDOW
# ================================================================

class SignalAnalyzerGUI(QMainWindow):

    NAV = [

        ("Dashboard", "⌂"),

        ("File Manager", "▦"),

        ("Signal Analysis", "◉"),

        ("Spectrum", "∿"),

        ("Waterfall", "≋"),

        ("Constellation", "◇"),

        ("Parameter Estimation", "≡"),

        ("Demodulation", "⇄"),

        ("Decoded Output", "▤"),

        ("Reports", "▧"),

        ("Settings", "⚙")
    ]

    def __init__(self):

        super().__init__()

        self.controller = AnalysisController()

        self.setWindowTitle(
            "NTRO Signal Intelligence Suite — "
            "Automated IQ/WAV Signal Analyzer & Demodulator Engine"
        )

        self.setMinimumSize(
            1280,
            760
        )

        self.resize(
            1540,
            920
        )

        self.setAcceptDrops(
            True
        )

        self.pages = {}

        self._build_ui()

        self._apply_style()

        self._refresh_system_status()

    # ============================================================
    # BUILD UI
    # ============================================================

    def _build_ui(self):

        root = QWidget()

        self.setCentralWidget(
            root
        )

        outer = QHBoxLayout(
            root
        )

        outer.setContentsMargins(
            0,
            0,
            0,
            0
        )

        outer.setSpacing(
            0
        )

        # ========================================================
        # SIDEBAR
        # ========================================================

        self.sidebar = QFrame()

        self.sidebar.setObjectName(
            "Sidebar"
        )

        self.sidebar.setFixedWidth(
            244
        )

        sidebar_layout = QVBoxLayout(
            self.sidebar
        )

        sidebar_layout.setContentsMargins(
            16,
            18,
            16,
            16
        )

        sidebar_layout.setSpacing(
            4
        )

        brand = QLabel(
            "NTRO\nSIGNAL INTELLIGENCE SUITE"
        )

        brand.setObjectName(
            "Brand"
        )

        sidebar_layout.addWidget(
            brand
        )

        sidebar_layout.addSpacing(
            14
        )

        self.nav_buttons = []

        for i, (name, icon) in enumerate(
            self.NAV
        ):

            button = QToolButton()

            button.setText(
                f"{icon}   {name}"
            )

            button.setObjectName(
                "NavButton"
            )

            button.setToolButtonStyle(
                Qt.ToolButtonTextOnly
            )

            button.setProperty(
                "active",
                i == 0
            )

            button.clicked.connect(
                lambda checked=False,
                idx=i:
                self.show_page(idx)
            )

            sidebar_layout.addWidget(
                button
            )

            self.nav_buttons.append(
                button
            )

        sidebar_layout.addStretch()

        # ========================================================
        # SYSTEM STATUS
        # ========================================================

        status = QFrame()

        status.setObjectName(
            "SystemStatus"
        )

        status_layout = QVBoxLayout(
            status
        )

        status_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        title = QLabel(
            "SYSTEM STATUS"
        )

        title.setObjectName(
            "TinyLabel"
        )

        status_layout.addWidget(
            title
        )

        self.status_labels = {}

        for key in [

            "DSP Engine",
            "File Engine",
            "ML Engine",
            "GPU",
            "Version"

        ]:

            row = QHBoxLayout()

            label = QLabel(
                key
            )

            label.setObjectName(
                "StatusKey"
            )

            value = QLabel(
                "—"
            )

            value.setObjectName(
                "StatusValue"
            )

            row.addWidget(
                label
            )

            row.addStretch()

            row.addWidget(
                value
            )

            status_layout.addLayout(
                row
            )

            self.status_labels[
                key
            ] = value

        sidebar_layout.addWidget(
            status
        )

        outer.addWidget(
            self.sidebar
        )

        # ========================================================
        # MAIN AREA
        # ========================================================

        main = QWidget()

        main_layout = QVBoxLayout(
            main
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ========================================================
        # HEADER
        # ========================================================

        header = QFrame()

        header.setObjectName(
            "Header"
        )

        header_layout = QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            20,
            12,
            20,
            12
        )

        left = QVBoxLayout()

        title = QLabel(
            "SIGNAL INTELLIGENCE APPLICATION"
        )

        title.setObjectName(
            "HeaderTitle"
        )

        subtitle = QLabel(
            "Analyze. Identify. Demodulate. Decode."
        )

        subtitle.setObjectName(
            "HeaderSub"
        )

        left.addWidget(
            title
        )

        left.addWidget(
            subtitle
        )

        header_layout.addLayout(
            left
        )

        header_layout.addStretch()

        self.header_file = QLabel(
            "NO ACTIVE SIGNAL"
        )

        self.header_file.setObjectName(
            "HeaderSignal"
        )

        header_layout.addWidget(
            self.header_file
        )

        open_button = QPushButton(
            "OPEN FILE"
        )

        open_button.clicked.connect(
            self.open_file_dialog
        )

        header_layout.addWidget(
            open_button
        )

        main_layout.addWidget(
            header
        )

        # ========================================================
        # BODY
        # ========================================================

        body = QWidget()

        body_layout = QVBoxLayout(
            body
        )

        body_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        body_layout.setSpacing(
            0
        )

        # --------------------------------------------------------
        # PROGRESS
        # --------------------------------------------------------

        progress_row = QHBoxLayout()

        progress_row.setContentsMargins(
            20,
            8,
            20,
            6
        )

        self.progress_label = QLabel(
            "Preparing analysis"
        )

        self.progress_label.setObjectName(
            "PanelMeta"
        )

        self.progress = QProgressBar()

        self.progress.setRange(
            0,
            100
        )

        self.progress.setValue(
            0
        )

        self.progress.setVisible(
            False
        )

        self.progress_label.setVisible(
            False
        )

        progress_row.addWidget(
            self.progress_label
        )

        progress_row.addWidget(
            self.progress,
            1
        )

        body_layout.addLayout(
            progress_row
        )

        # --------------------------------------------------------
        # STACK
        # --------------------------------------------------------

        self.stack = QStackedWidget()

        body_layout.addWidget(
            self.stack
        )

        main_layout.addWidget(
            body,
            1
        )

        outer.addWidget(
            main,
            1
        )

        # ========================================================
        # PAGES
        # ========================================================

        self.pages[0] = DashboardPage(
            self.controller,
            self
        )

        self.pages[1] = FilesPage(
            self.controller,
            self
        )

        self.pages[2] = AnalysisPage(
            self.controller,
            self
        )

        self.pages[3] = SpectrumPage(
            self.controller,
            self
        )

        self.pages[4] = WaterfallPage(
            self.controller,
            self
        )

        self.pages[5] = ConstellationPage(
            self.controller,
            self
        )

        self.pages[6] = ParametersPage(
            self.controller,
            self
        )

        self.pages[7] = DemodPage(
            self.controller,
            self
        )

        self.pages[8] = OutputPage(
            self.controller,
            self
        )

        self.pages[9] = ReportsPage(
            self.controller,
            self
        )

        self.pages[10] = SettingsPage(
            self.controller,
            self
        )

        for i in range(
            len(self.NAV)
        ):

            self.stack.addWidget(
                self.pages[i]
            )

        self.show_page(
            0
        )

    # ============================================================
    # SYSTEM STATUS
    # ============================================================

    def _refresh_system_status(self):

        self.status_labels[
            "DSP Engine"
        ].setText(
            "ONLINE"
        )

        self.status_labels[
            "DSP Engine"
        ].setStyleSheet(
            f"color:{GREEN};"
        )

        self.status_labels[
            "File Engine"
        ].setText(
            "ONLINE"
        )

        self.status_labels[
            "File Engine"
        ].setStyleSheet(
            f"color:{GREEN};"
        )

        self.status_labels[
            "ML Engine"
        ].setText(
            "STANDBY"
        )

        self.status_labels[
            "ML Engine"
        ].setStyleSheet(
            f"color:{ORANGE};"
        )

        try:

            import torch

            gpu = (
                "AVAILABLE"
                if torch.cuda.is_available()
                else
                "OFFLINE"
            )

        except Exception:

            gpu = "UNAVAILABLE"

        self.status_labels[
            "GPU"
        ].setText(
            gpu
        )

        self.status_labels[
            "GPU"
        ].setStyleSheet(

            f"color:"
            f"{BLUE if gpu == 'AVAILABLE' else GRAY};"
        )

        self.status_labels[
            "Version"
        ].setText(
            "1.0.0"
        )

        self.status_labels[
            "Version"
        ].setStyleSheet(
            f"color:{MUTED};"
        )

    # ============================================================
    # APPLICATION STYLE
    # ============================================================

    def _apply_style(self):

        self.setStyleSheet(
            f"""

            /* ====================================================
               GLOBAL TYPOGRAPHY
               ==================================================== */

            QWidget {{
                font-family:
                    "IBM Plex Sans",
                    "Segoe UI",
                    Arial,
                    sans-serif;

                color: {TEXT};

                font-size: 13px;
            }}

            QMainWindow {{
                background: {BG};
            }}


            /* ====================================================
               SIDEBAR
               ==================================================== */

            #Sidebar {{
                background: {WHITE};
                border-right: 1px solid {BORDER};
            }}

            #Brand {{
                color: {NAVY};

                font-family:
                    "IBM Plex Sans",
                    "Segoe UI",
                    sans-serif;

                font-weight: 700;

                font-size: 14px;

                letter-spacing: 1px;

                padding: 4px;
            }}

            #NavButton {{
                text-align: left;

                border: 0;

                padding: 10px 12px;

                color: #475569;

                background: transparent;

                border-radius: 3px;

                font-weight: 600;

                font-size: 12px;
            }}

            #NavButton:hover {{
                background: #F8FAFC;

                color: {CHARCOAL};
            }}

            #NavButton[active="true"] {{
                background: {ORANGE_SOFT};

                color: {ORANGE_DARK};

                border-left:
                    3px solid {ORANGE};
            }}


            /* ====================================================
               HEADER
               ==================================================== */

            #Header {{
                background: {WHITE};

                border-bottom:
                    1px solid {BORDER};
            }}

            #HeaderTitle {{
                color: {NAVY};

                font-weight: 700;

                font-size: 13px;

                letter-spacing: 1px;
            }}

            #HeaderSub {{
                color: {MUTED};

                font-size: 10px;
            }}

            #HeaderSignal,
            #SignalPill {{
                background: {ORANGE_SOFT};

                color: {ORANGE_DARK};

                border:
                    1px solid #FED7AA;

                padding: 6px 10px;

                border-radius: 3px;

                font-weight: 700;

                font-size: 11px;
            }}


            /* ====================================================
               PAGE
               ==================================================== */

            #PageTitle {{
                color: {CHARCOAL};

                font-family:
                    "IBM Plex Sans",
                    "Segoe UI",
                    sans-serif;

                font-size: 22px;

                font-weight: 700;
            }}

            #PageSubtitle {{
                color: {MUTED};

                font-size: 11px;
            }}


            /* ====================================================
               PANELS
               ==================================================== */

            #Panel {{
                background: {WHITE};

                border:
                    1px solid {BORDER};

                border-radius: 5px;
            }}

            #PanelTitle {{
                color: {NAVY};

                font-size: 11px;

                font-weight: 700;

                letter-spacing: 1px;
            }}

            #PanelMeta {{
                color: {MUTED};

                font-size: 11px;
            }}


            /* ====================================================
               METRICS
               ==================================================== */

            #MetricTitle,
            #TinyLabel {{
                color: {MUTED};

                font-size: 9px;

                font-weight: 700;

                letter-spacing: 1px;
            }}

            #MetricValue {{
                color: {CHARCOAL};

                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 20px;

                font-weight: 700;
            }}

            #MetricStatus {{
                font-size: 9px;

                font-weight: 700;

                letter-spacing: 0.8px;
            }}

            #TechValue {{
                color: {CHARCOAL};

                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 11px;

                font-weight: 600;
            }}


            /* ====================================================
               DASHBOARD
               ==================================================== */

            #DashboardInput {{
                background: {WHITE};

                border:
                    1px solid {BORDER};
            }}

            #DashboardDropZone {{
                background: {ORANGE_SOFT};

                border:
                    1px dashed #FDBA74;

                border-radius: 4px;
            }}

            #AcquisitionLabel {{
                color: {ORANGE_DARK};

                font-size: 9px;

                font-weight: 800;

                letter-spacing: 1.2px;
            }}

            #DropTitle {{
                color: {CHARCOAL};

                font-size: 17px;

                font-weight: 700;
            }}

            #MetadataFrame {{
                background: #FAFAFA;

                border:
                    1px solid {BORDER};

                border-radius: 4px;
            }}

            #DashboardFooter {{
                background: #F8FAFC;

                border:
                    1px solid {BORDER};

                border-radius: 4px;
            }}

            #WorkflowStatus,
            #ValidationStatus {{
                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 9px;

                font-weight: 700;

                letter-spacing: 0.5px;

                color: {MUTED};
            }}


            /* ====================================================
               BUTTONS
               ==================================================== */

            QPushButton {{
                background: {ORANGE};

                color: white;

                border: 0;

                border-radius: 3px;

                padding: 8px 13px;

                font-weight: 700;

                font-size: 11px;
            }}

            QPushButton:hover {{
                background: {ORANGE_DARK};
            }}

            #PrimaryAnalyzeButton {{
                background: {ORANGE};

                padding-left: 16px;

                padding-right: 16px;
            }}

            #SecondaryButton {{
                background: {WHITE};

                color: {CHARCOAL};

                border:
                    1px solid {BORDER};
            }}

            #SecondaryButton:hover {{
                background: #F8FAFC;

                border-color: #CBD5E1;
            }}


            /* ====================================================
               INPUT CONTROLS
               ==================================================== */

            QComboBox,
            QSpinBox,
            QDoubleSpinBox,
            QLineEdit {{
                background: {WHITE};

                border:
                    1px solid {BORDER};

                padding: 6px;

                border-radius: 3px;

                font-size: 11px;
            }}

            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus,
            QLineEdit:focus {{
                border:
                    1px solid #FDBA74;
            }}


            /* ====================================================
               TABLES
               ==================================================== */

            QTableWidget {{
                background: {WHITE};

                border:
                    1px solid {BORDER};

                gridline-color:
                    {BORDER};

                alternate-background-color:
                    #FAFAFA;

                font-size: 11px;
            }}

            QHeaderView::section {{
                background: #F8FAFC;

                color: {MUTED};

                padding: 8px;

                border: 0;

                border-bottom:
                    1px solid {BORDER};

                font-size: 9px;

                font-weight: 800;

                letter-spacing: 0.7px;
            }}


            /* ====================================================
               TERMINAL
               ==================================================== */

            #Terminal,
            #BitTerminal {{
                background: #0F172A;

                color: #E2E8F0;

                border: 0;

                border-radius: 3px;

                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 10px;

                padding: 10px;
            }}

            #WorkflowLabel {{
                background: #F8FAFC;

                border:
                    1px solid {BORDER};

                padding: 14px;

                color: {NAVY};

                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 10px;
            }}

            #TechnicalReadout {{
                color: {MUTED};

                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                padding: 5px;

                font-size: 10px;
            }}


            /* ====================================================
               DEMODULATION
               ==================================================== */

            #StageBox {{
                background: #FAFAFA;

                border:
                    1px solid {BORDER};

                border-radius: 3px;
            }}

            #StageStatus {{
                color: {MUTED};

                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 10px;

                font-weight: 700;
            }}


            /* ====================================================
               TABS
               ==================================================== */

            QTabWidget::pane {{
                border:
                    1px solid {BORDER};

                background: {WHITE};
            }}

            QTabBar::tab {{
                padding: 8px 15px;

                color: {MUTED};

                font-size: 11px;
            }}

            QTabBar::tab:selected {{
                color: {ORANGE_DARK};

                border-bottom:
                    2px solid {ORANGE};

                font-weight: 700;
            }}


            /* ====================================================
               PROGRESS
               ==================================================== */

            QProgressBar {{
                background: #E2E8F0;

                border: 0;

                height: 5px;

                text-align: center;
            }}

            QProgressBar::chunk {{
                background: {ORANGE};
            }}


            /* ====================================================
               SYSTEM STATUS
               ==================================================== */

            #SystemStatus {{
                background: #F8FAFC;

                border:
                    1px solid {BORDER};

                border-radius: 4px;
            }}

            #StatusKey {{
                color: {MUTED};

                font-size: 9px;
            }}

            #StatusValue {{
                font-family:
                    "IBM Plex Mono",
                    "Consolas",
                    monospace;

                font-size: 9px;

                font-weight: 700;
            }}
            """
        )

    # ============================================================
    # PAGE SWITCHING
    # ============================================================

    def show_page(
        self,
        index
    ):

        self.stack.setCurrentIndex(
            index
        )

        for i, button in enumerate(
            self.nav_buttons
        ):

            button.setProperty(
                "active",
                i == index
            )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

        if index == 1:

            self.pages[
                1
            ].refresh()

        page = self.pages.get(
            index
        )

        if (
            page
            and
            hasattr(
                page,
                "update_from_results"
            )
        ):

            page.update_from_results()

    # ============================================================
    # OPEN FILE
    # ============================================================

    def open_file_dialog(self):

        path, _ = QFileDialog.getOpenFileName(

            self,

            "Open IQ / WAV Signal",

            "",

            "Signal Files (*.iq *.wav *.dat);;"
            "All Files (*)"
        )

        if path:

            self.load_file(
                path
            )

    # ============================================================
    # LOAD FILE
    # ============================================================

    def load_file(
        self,
        path
    ):

        try:

            fmt = (
                self.pages[0]
                .format_combo
                .currentText()
            )

            meta = self.controller.load_signal(
                path,
                fmt
            )

            self.header_file.setText(
                meta["file_name"]
            )

            self.pages[
                0
            ].drop_text.setText(
                meta["file_name"]
            )

            self.pages[
                0
            ].drop_meta.setText(

                f"{meta['file_type']}"
                f" · "
                f"{meta['sampling_rate_text']}"
                f" · "
                f"{meta['duration_text']}"
            )

            self.pages[
                0
            ].update_from_results()

            self.pages[
                1
            ].refresh()

            self.show_page(
                0
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Signal Load Error",
                str(exc)
            )

    # ============================================================
    # ANALYZE
    # ============================================================

    def analyze_current(self):

        if self.controller.signal_data is None:

            QMessageBox.information(
                self,
                "No Signal",
                "Open an IQ/WAV file before analysis."
            )

            return

        self._set_progress(
            True,
            0,
            "Preparing signal"
        )

        try:

            self.controller.analyze_signal(
                self._progress
            )

            self._set_progress(
                False,
                100,
                "Analysis complete"
            )

            self.update_all_pages()

            self.show_page(
                0
            )

        except Exception as exc:

            self._set_progress(
                False,
                0,
                "Analysis failed"
            )

            QMessageBox.critical(
                self,
                "Analysis Error",
                str(exc)
            )

    # ============================================================
    # PROGRESS
    # ============================================================

    def _progress(
        self,
        value,
        stage
    ):

        if hasattr(
            self,
            "progress"
        ):

            self.progress.setValue(
                value
            )

            self.progress_label.setText(
                f"{stage} · {value}%"
            )

            QApplication.processEvents()

    def _set_progress(
        self,
        visible,
        value,
        stage
    ):

        self.progress.setVisible(
            visible
        )

        self.progress_label.setVisible(
            visible
        )

        self.progress.setValue(
            value
        )

        self.progress_label.setText(
            stage
        )

        QApplication.processEvents()

    # ============================================================
    # UPDATE ALL PAGES
    # ============================================================

    def update_all_pages(self):

        self.header_file.setText(

            self.controller.metadata().get(
                "file_name",
                "NO ACTIVE SIGNAL"
            )
        )

        for page in self.pages.values():

            if hasattr(
                page,
                "update_from_results"
            ):

                page.update_from_results()

    # ============================================================
    # EXPORT JSON
    # ============================================================

    def export_json(self):

        if not self.controller.results:
            return

        path, _ = QFileDialog.getSaveFileName(

            self,

            "Export JSON",

            "signal_analysis.json",

            "JSON (*.json)"
        )

        if not path:
            return

        r = self.controller.results

        output = {}

        for key, value in r.items():

            if isinstance(
                value,
                np.ndarray
            ):

                continue

            if isinstance(
                value,
                (
                    np.floating,
                    np.integer
                )
            ):

                value = value.item()

            output[key] = value

        output["file"] = (
            self.controller.metadata()
        )

        output["candidates"] = (
            r["candidates"]
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                output,
                f,
                indent=2,
                default=str
            )

    # ============================================================
    # EXPORT PDF
    # ============================================================

    def export_pdf(self):

        if not self.controller.results:
            return

        path, _ = QFileDialog.getSaveFileName(

            self,

            "Generate PDF Report",

            "signal_analysis_report.pdf",

            "PDF (*.pdf)"
        )

        if not path:
            return

        r = self.controller.results

        m = self.controller.metadata()

        html = f"""

        <html>

        <body
            style="
                font-family:Arial;
                color:#111827;
            "
        >

        <h1>
            Signal Intelligence Analysis Report
        </h1>

        <p>
            <b>File:</b>
            {m.get('file_name', '—')}
        </p>

        <hr>

        <h2>
            Signal Summary
        </h2>

        <p>

            Samples:
            {m.get('samples', '—'):,}

            <br>

            Sampling Rate:
            {m.get('sampling_rate_text', '—')}

            <br>

            Duration:
            {m.get('duration_text', '—')}

            <br>

            SNR:
            {r['snr']:.2f} dB

            <br>

            Bandwidth:
            {r['bandwidth']:.3f} Hz

            <br>

            Peak Frequency:
            {r['peak_frequency']:.3f} Hz

            <br>

            Symbol Rate:
            {r['baud']:.2f} Baud

            <br>

            Modulation Candidate:
            {r['modulation']}

            <br>

            Confidence:
            {r['confidence'] * 100:.2f}%

        </p>

        <h2>
            Validation
        </h2>

        <p>

            Preamble:
            {r['preamble_name'] or 'N/A'}

            <br>

            Confidence:
            {r['preamble_confidence'] * 100:.2f}%

            <br>

            FEC:
            {r['fec']}

            <br>

            Interleaving:
            {r['interleaving']}

            <br>

            Frame Status:
            {r['validation']}

        </p>

        </body>

        </html>
        """

        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setOutputFormat(
            QPrinter.PdfFormat
        )

        printer.setOutputFileName(
            path
        )

        from PyQt5.QtGui import QTextDocument

        document = QTextDocument()

        document.setHtml(
            html
        )

        document.print_(
            printer
        )

    # ============================================================
    # DRAG ENTER
    # ============================================================

    def dragEnterEvent(
        self,
        event
    ):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()

    # ============================================================
    # DROP FILE
    # ============================================================

    def dropEvent(
        self,
        event
    ):

        urls = event.mimeData().urls()

        if urls:

            self.load_file(
                urls[0].toLocalFile()
            )


# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "NTRO Signal Intelligence Suite"
    )

    # ============================================================
    # GLOBAL FONT
    # ============================================================

    app.setFont(
        QFont(
            "IBM Plex Sans",
            10
        )
    )

    window = SignalAnalyzerGUI()

    window.show()

    sys.exit(
        app.exec_()
    )


# ================================================================
# RUN
# ================================================================

if __name__ == "__main__":

    main()


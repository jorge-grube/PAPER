// build_paper_ECONOMIES.js — MDPI Economies manuscript (FULL + BLINDED versions)
// Special Issue: "Next-Generation Macroeconomics: Data-Driven and Artificial Intelligence Approaches"
// Title: "From Regime Detection to Decision Rules: A Data-Driven Macro-Financial CVaR
//         Framework for European Multi-Asset Portfolios"
// Built from paper_draft_FINAL.js; major changes:
//  - MDPI structure: numbered sections (1-5), MDPI back matter, author-date references
//  - Abstract rewritten ~175 words (MDPI style, no headings)
//  - Keywords: 8 (data-driven macroeconomics, HMM, CVaR, systemic risk, etc.)
//  - Section 1: Introduction (Economies/AI-macro framing)
//  - Section 2: Materials and Methods (merged Data + Methodology)
//  - Section 3: Results (6 subsections, Tables 1-10, Figures 1-5)
//  - Section 4: Discussion (expanded for Economies, AI/data-driven macro angle)
//  - Section 5: Conclusions
//  - MDPI back matter (Author Contributions, Funding, DAS, etc.)
//  - All tables renumbered Table 1-10; figures Figure 1-5
//  - No JF running head; MDPI header
//  - No JEL classification in front matter
//  - Outputs: FULL (with author) and BLINDED (peer review) versions
// Run: node build_paper_ECONOMIES.js
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, AlignmentType, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat, TabStopType,
} = require('./node_modules/docx');
const fs   = require('fs');
const path = require('path');

// --- Figure paths ---
// v7 figure numbering:
//   Figure 1 = methodology workflow (new)
//   Figure 2 = HMM state characteristics bar chart
//   Figure 3 = full-sample HMM regime timeline
//   Figure 4 = cumulative wealth, Panel B
//   Figure 5 = turnover vs net Sharpe frontier
//   Figure 6 = average weights, baseline vs FI-expanded
//   Figure 7 = drawdown comparison, baseline vs FI-expanded
const FIG_DIR = require('path').join(__dirname, 'figures') + '/';
const FIG = {
  f1:  fs.readFileSync(FIG_DIR + 'figure_0_methodology_workflow.png'),
  f2s: fs.readFileSync(FIG_DIR + 'figure_2_hmm_state_characteristics.png'),
  f3:  fs.readFileSync(FIG_DIR + 'figure_1_regime_timeline.png'),
  f4:  fs.readFileSync(FIG_DIR + 'figure_2_cumulative_wealth_panel_b.png'),
  f5:  fs.readFileSync(FIG_DIR + 'figure_3_turnover_vs_net_sharpe.png'),
  f6:  fs.readFileSync(FIG_DIR + 'figure_4_static_cvar_weights_baseline_vs_fi.png'),
  f7:  fs.readFileSync(FIG_DIR + 'figure_5_drawdown_baseline_vs_fi.png'),
};

// --- Layout: MDPI Economies template (A4) ---
// A4: 11906 x 16838 DXA; margins: left/right 720, top 1417, bottom 907
// Body indent (MDPI gutter): 2608 DXA (makes 2-column-look with journal info on left)
const PAGE_W      = 11906;   // A4 width
const PAGE_H      = 16838;   // A4 height
const SIDE_MARGIN = 720;     // 0.5 inch
const TB_MARGIN   = 1417;    // 0.984 inch top
const BOT_MARGIN  = 907;     // 0.630 inch bottom
const CONTENT     = PAGE_W - 2 * SIDE_MARGIN; // 10466 DXA
const BODY_INDENT = 2608;    // MDPI text column left indent
const FIRST_INDENT = 425;    // first-line paragraph indent (~0.3 inch)

// --- Helpers ---
function run(text, opts = {}) {
  return new TextRun({
    text,
    font: opts.font || 'Palatino Linotype',
    size: opts.size || 20,
    bold: opts.bold || false,
    italics: opts.italics || false,
    superScript: opts.sup || false,
  });
}

function bodyPara(children, opts = {}) {
  const kids = Array.isArray(children) ? children : [run(children)];
  return new Paragraph({
    children: kids,
    alignment: AlignmentType.JUSTIFIED,
    spacing: { before: 0, after: 0, line: 280, lineRule: 'atLeast' },
    indent: { left: BODY_INDENT, firstLine: FIRST_INDENT },
    keepNext: opts.keepNext || false,
  });
}

function blankLine() {
  // Zero-height spacer — used between paragraphs; no visible gap (MDPI style).
  // Figures, tables, and equations carry their own before/after spacing.
  return new Paragraph({
    children: [new TextRun({ text: '', font: 'Palatino Linotype', size: 2 })],
    spacing: { before: 0, after: 0 },
  });
}

function sectionHeading(num, title) {
  return new Paragraph({
    children: [run(num ? `${num} ${title}` : title, { bold: true, size: 24 })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 240, after: 60, line: 280, lineRule: 'atLeast' },
    indent: { left: BODY_INDENT },
  });
}

function subHeading(num, title) {
  return new Paragraph({
    children: [run(num ? `${num} ${title}` : title, { italics: true, size: 20 })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 60, after: 60, line: 280, lineRule: 'atLeast' },
    indent: { left: BODY_INDENT },
  });
}

function sub3Heading(num, title) {
  return new Paragraph({
    children: [run(num ? `${num} ${title}` : title, { size: 20 })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 60, after: 60, line: 280, lineRule: 'atLeast' },
    indent: { left: BODY_INDENT },
  });
}

function pageBreakPara() {
  return new Paragraph({ children: [new PageBreak()], spacing: { before: 0, after: 0 } });
}

// Equation paragraphs: Palatino Linotype, indented per MDPI spec
function eqPara(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: 'Palatino Linotype', size: 20, italics: false })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 120, after: 120, line: 280, lineRule: 'atLeast' },
    indent: { left: BODY_INDENT },
  });
}

// Placeholder paragraph for OMML injection (post-processing step)
function ommlPara(marker) {
  return new Paragraph({
    children: [new TextRun({ text: marker, font: 'Palatino Linotype', size: 20 })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 120, after: 120, line: 280, lineRule: 'atLeast' },
    indent: { left: BODY_INDENT },
  });
}

// --- Figure image paragraph ---
// Figures span the full content width (same as tables) with no body indent
function figImage(imgData, origW, origH, altTitle) {
  // CONTENT DXA -> pixels at 96 dpi (docx-js transformation uses 96-dpi pixels)
  const dispW = Math.round(CONTENT / 1440 * 96); // ~698 pixels = 7.27 inches
  const H = Math.round(origH * dispW / origW);
  return new Paragraph({
    children: [new ImageRun({
      type: 'png',
      data: imgData,
      transformation: { width: dispW, height: H },
      altText: { title: altTitle, description: altTitle, name: altTitle },
    })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 120, after: 120 },
    indent: { left: 0 },
  });
}

// --- Table helpers ---
const TB  = { style: BorderStyle.SINGLE, size: 6,  color: '000000' };
const TBT = { style: BorderStyle.SINGLE, size: 12, color: '000000' };
const TNB = { style: BorderStyle.NIL,    size: 0,  color: 'ffffff' };

function tcell(text, opts = {}) {
  const {
    bold = false, italics = false, align = AlignmentType.CENTER,
    width, borders, colspan = 1, size = 20,
  } = opts;
  const cellBorders = borders || { top: TNB, bottom: TNB, left: TNB, right: TNB };
  return new TableCell({
    columnSpan: colspan,
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    borders: cellBorders,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [new Paragraph({
      children: [new TextRun({ text, font: 'Palatino Linotype', size, bold, italics })],
      alignment: align,
      spacing: { before: 0, after: 0, line: 240, lineRule: 'auto' },
    })],
  });
}

// Table caption: number on its own line, title on next line, note below
// Keeps next element (the table) together
function tblCaption(label, title, note) {
  // MDPI_4.1_table_caption: 9pt Palatino, left indent 2608, before 240, after 120
  const paras = [
    new Paragraph({
      children: [run(label + '. ' + title, { bold: false, size: 18 })],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 240, after: 120, line: 280, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT },
      keepNext: true,
    }),
  ];
  if (note) {
    paras.push(new Paragraph({
      children: [run(note, { size: 16 })],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 60, line: 260, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT },
      keepNext: true,
    }));
  }
  return paras;
}

// Figure caption: "Figure N. [note]" — no separate title per author preference
function figCaption(label, title, note) {
  // MDPI_5.1_figure_caption: 9pt Palatino, left indent 2608, before 120, after 240
  // Title omitted; format: "Figure N. Note."
  let captionText = label + '.';
  if (note) captionText += ' ' + note;
  return [
    new Paragraph({
      children: [run(captionText, { size: 18 })],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 120, after: 240, line: 280, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT },
    }),
  ];
}

// --- MDPI FRONT MATTER ---
function buildFrontMatter(blinded = false) {
  // MDPI Economies template layout:
  // MDPI_1.1_article_type: 10pt Palatino, before 240, left-aligned
  // MDPI_1.2_title: 18pt bold Palatino, left-aligned
  // MDPI_1.3_authornames: 10pt bold Palatino, left-aligned
  // MDPI_1.6_affiliation: 8pt Palatino, hanging indent 198, left indent 2806
  // MDPI_1.7_abstract: 10pt, justified, left indent 2608, before 240 after 120
  // MDPI_1.8_keywords: 10pt, justified, left indent 2608, before 240
  const abstractText =
    'Weekly macro-financial and financial-market data, combined with machine-learning methods, offer new possibilities ' +
    'for identifying latent economic states in real time, but the portfolio value of regime ' +
    'detection depends critically on how detected states are translated into allocation rules. ' +
    'This paper develops and evaluates a data-driven macro-financial framework that combines a ' +
    'four-state Gaussian Hidden Markov Model (HMM), estimated on eight weekly macro-financial ' +
    'features, with Conditional Value-at-Risk (CVaR) portfolio optimization across European ' +
    'multi-asset portfolios from January 2000 to April 2026. Using a strictly out-of-sample ' +
    'walk-forward design, we show that naive regime-conditional CVaR allocation generates ' +
    'excessive turnover that erodes net performance under any realistic transaction cost, while ' +
    'implementation-aware alternatives recover the performance gap substantially. Expanding the ' +
    'universe to include sovereign bonds improves drawdown control but introduces duration risk ' +
    'that materializes in rate-hiking episodes. These findings demonstrate that, in data-driven ' +
    'macro-financial systems, the bottleneck is not regime detection but transparent, stable, ' +
    'and cost-aware decision-rule design.';

  return [
    // Article type — MDPI_1.1 (10pt, before 240)
    new Paragraph({
      children: [run('Article', { italics: true, size: 20 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 240, after: 0, line: 280, lineRule: 'atLeast' },
    }),
    // Title — MDPI_1.2 (18pt bold, left-aligned, after 240)
    new Paragraph({
      children: [run(
        'From Regime Detection to Decision Rules: A Data-Driven Macro-Financial ' +
        'CVaR Framework for European Multi-Asset Portfolios',
        { size: 36, bold: true }
      )],
      alignment: AlignmentType.LEFT,
      spacing: { before: 0, after: 240, line: 240, lineRule: 'atLeast' },
    }),
    // Author(s) — MDPI_1.3 (10pt bold, after 360)
    ...(blinded ? [
      new Paragraph({
        children: [run('[Author details removed for peer review]', { italics: true, size: 20 })],
        alignment: AlignmentType.LEFT,
        spacing: { before: 0, after: 360, line: 260, lineRule: 'atLeast' },
      }),
    ] : [
      new Paragraph({
        children: [run('Jorge Grube', { bold: true, size: 20 })],
        alignment: AlignmentType.LEFT,
        spacing: { before: 0, after: 360, line: 260, lineRule: 'atLeast' },
      }),
      // Affiliation — MDPI_1.6 (8pt, hanging indent)
      new Paragraph({
        children: [
          run('1  ', { size: 16 }),
          run('Faculty of Economics and Business, Universidad Francisco de Vitoria, ' +
            'Carretera Pozuelo-Majadahonda, km. 1.800, Pozuelo de Alarcon, 28223 Madrid, Spain; ' +
            'jorgegrubeml@gmail.com', { size: 16 }),
        ],
        alignment: AlignmentType.LEFT,
        spacing: { before: 0, after: 0, line: 200, lineRule: 'atLeast' },
        indent: { left: 198, hanging: 198 },
      }),
      new Paragraph({
        children: [run('* Correspondence: jorgegrubeml@gmail.com', { size: 16 })],
        alignment: AlignmentType.LEFT,
        spacing: { before: 0, after: 0, line: 200, lineRule: 'atLeast' },
      }),
    ]),
    blankLine(),
    // Abstract — MDPI_1.7 (10pt, justified, left indent 2608, label on same paragraph)
    new Paragraph({
      children: [
        run('Abstract: ', { bold: true, size: 20 }),
        run(abstractText, { size: 20 }),
      ],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 240, after: 120, line: 280, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT },
    }),
    // Keywords — MDPI_1.8 (10pt, justified, left indent 2608)
    new Paragraph({
      children: [
        run('Keywords: ', { bold: true, size: 20 }),
        run('data-driven macroeconomics; macro-financial regimes; Hidden Markov Model; ' +
          'Conditional Value-at-Risk; systemic risk; interest rates; portfolio allocation; ' +
          'implementation frictions', { size: 20 }),
      ],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 240, after: 0, line: 280, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT },
    }),
    // JEL Classification — per MDPI Economies journal requirement
    new Paragraph({
      children: [
        run('JEL Classification: ', { bold: true, size: 20 }),
        run('G11; G12; C22', { size: 20 }),
      ],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 120, after: 0, line: 280, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT },
    }),
    blankLine(),
    pageBreakPara(),
  ];
}

// --- SECTION 1: INTRODUCTION ---
function buildSection1() {
  return [
    sectionHeading('1.', 'Introduction'),
    // Para 1: Macro motivation, AI/data-driven methods
    bodyPara(
      'The increasing availability of weekly macro-financial and financial-market data and the development ' +
      'of machine-learning methods for economic analysis have opened new possibilities for ' +
      'identifying latent economic states in real time (Gu et al., 2020). From traditional ' +
      'Hamilton (1989) and Rabiner (1989) Hidden Markov Models for business-cycle identification to ' +
      'data-rich macroeconomic nowcasting frameworks (Bernanke and Boivin, 2003), the common premise is that ' +
      'financial and economic processes cycle through distinct regimes with different statistical properties. In the context ' +
      'of portfolio risk management, such regime information is potentially valuable: an ' +
      'allocation framework that can adapt to changing macroeconomic conditions, such as ' +
      'volatile-stress episodes, sovereign-spread crises, or inflation surges, may achieve ' +
      'better risk-adjusted outcomes than a static, regime-unconditional approach. Yet the ' +
      'empirical evidence on whether regime-conditioned portfolio strategies deliver out-of-' +
      'sample improvements remains mixed, and implementation frictions have received ' +
      'comparatively little systematic attention in the data-driven macroeconomics literature.'
    ),
    blankLine(),
    // Para 2: Regime detection for macro-financial analysis and systemic risk
    bodyPara(
      'Regime detection is directly relevant to macro-financial surveillance and systemic ' +
      'risk monitoring (Billio et al., 2012; Adrian and Brunnermeier, 2016). The states identified by Hidden Markov Models ' +
      '(HMMs) estimated on macro-financial features such as implied volatility indices, ' +
      'sovereign credit spreads, yield-curve slope, and inflation measures, correspond to ' +
      'recognizable economic episodes: low-volatility expansion phases, broad risk-on ' +
      'regimes, neutral moderate states, and elevated-risk stress periods characterized by ' +
      'financial market distress and widening peripheral spreads. Such classifications ' +
      'provide a transparent, data-driven taxonomy of macro-financial conditions that ' +
      'complements traditional business-cycle dating and can be computed in near-real time. ' +
      'From a systemic risk perspective, the ability to characterize stress regimes, ' +
      'and quantify the uncertainty in those labels, is a prerequisite for adaptive risk ' +
      'management in next-generation macro-financial systems.'
    ),
    blankLine(),
    // Para 3: Detection is not the same as decision-making
    bodyPara(
      'However, regime detection is not equivalent to regime-based decision-making. ' +
      'The central question is not only whether regimes can be detected, but whether ' +
      'detected regimes can be translated into transparent, stable, and low-turnover ' +
      'decision rules. In portfolio optimization, regime transitions can trigger ' +
      'discontinuous changes in the optimization problem, generating excessive rebalancing ' +
      'that erodes any gross performance advantage through transaction costs. ' +
      'This implementation friction is a structural feature of regime-conditional ' +
      'allocation, not an incidental artifact: it arises because the optimal solution ' +
      'for one regime\'s scenario set may differ substantially from the optimal solution ' +
      'for an adjacent regime\'s set, and because the HMM assigns new labels at every ' +
      'rebalance step. Understanding exactly when and why this friction dominates ' +
      'detection quality, and how implementation-aware design can overcome it, is the ' +
      'central methodological contribution of this paper.'
    ),
    blankLine(),
    // Para 4: European context
    bodyPara(
      'The European multi-asset setting provides a particularly demanding test environment. ' +
      'Europe has experienced four structurally distinct macro episodes within a single ' +
      '26-year window studied here: the post-dot-com normalization of 2002 to 2006; the ' +
      'Global Financial Crisis of 2008 to 2009, during which European equity indices lost ' +
      'approximately 50% to 60%; the European sovereign debt crisis of 2011 to 2012, ' +
      'characterized by peripheral spread widening and ECB unconventional policy interventions; ' +
      'and the COVID-19 crash of March 2020, followed by the post-zero-interest-rate ' +
      'transition of 2022 in which ECB rate hikes by 250 basis points imposed severe losses ' +
      'on long-duration bonds. Each episode rewarded a different defensive allocation: ' +
      'commodities and gold in 2008, government bonds in 2011, and commodity positions ' +
      'again in 2022. This structural instability in the cross-asset correlation regime ' +
      '(Longin and Solnik, 2001), combined with the presence of rate-shock and sovereign-spread dynamics absent in ' +
      'typical US-centric analyses, makes Europe an informative and challenging test bed ' +
      'for evaluating data-driven macro-financial allocation frameworks.'
    ),
    blankLine(),
    // Para 5: Research design
    bodyPara(
      'This paper develops and evaluates a transparent data-driven regime framework ' +
      'combining Conditional Value-at-Risk (CVaR) portfolio optimization with a four-state ' +
      'Gaussian HMM estimated on eight weekly macro-financial features, applied to ten ' +
      'risky European assets over January 2000 to April 2026. The HMM generates strictly ' +
      'out-of-sample regime labels via an expanding walk-forward procedure that re-estimates ' +
      'the model at each four-week rebalance step, ensuring no forward-looking information ' +
      'enters portfolio construction. We evaluate naive regime-conditioned CVaR (restricting ' +
      'the scenario set to regime-matched historical returns), implementation-aware alternatives ' +
      '(turnover-penalized LP and regime-constrained weight bands), and a 14-asset ' +
      'fixed-income expansion adding sovereign bond indices from Germany, Spain, and Italy.'
    ),
    blankLine(),
    // Para 6: Main findings (detection succeeds; translation fails)
    bodyPara(
      'The results indicate that the main bottleneck is not the identification of regimes, but ' +
      'their translation into stable, low-cost allocation rules. The walk-forward HMM produces ' +
      'locally stable, economically interpretable labels, yet naive regime-conditional scenario ' +
      'filtering generates implementation frictions that erode out-of-sample performance. ' +
      'Implementation-aware designs reduce this friction substantially. The fixed-income expansion ' +
      'shows that the defensive channel depends strongly on the asset universe and the prevailing ' +
      'interest-rate environment.'
    ),
    blankLine(),
    // Para 7: Contributions to data-driven macroeconomics
    bodyPara(
      'This paper makes three distinct contributions to the literature on next-generation ' +
      'data-driven macroeconomic systems. First, it provides the first strictly out-of-sample ' +
      'evaluation of regime-conditional CVaR specifically designed to isolate the role of ' +
      'implementation friction, extending Guidolin and Timmermann (2007) and Ang and Bekaert ' +
      '(2004) to the question of decision-rule design, an aspect almost entirely absent from ' +
      'prior empirical regime-portfolio work. Second, it identifies the LP scenario discontinuity ' +
      'as the structural mechanism behind regime CVaR failure: this diagnostic insight directly ' +
      'informs the design of AI-assisted macro-financial monitoring systems, where accurate state ' +
      'detection alone is not sufficient and the decision layer must be explicitly engineered for ' +
      'cost efficiency and stability. Third, it introduces regime-constrained weight bands as an ' +
      'institutionally viable bridge between macro-state detection and portfolio implementation, ' +
      'achieving near-benchmark risk-adjusted performance at a fraction of the turnover cost. ' +
      'Together, these contributions provide a practical blueprint for the next generation of ' +
      'data-driven allocation frameworks operating under real-world transaction costs and ' +
      'macro-financial regime uncertainty.'
    ),
    blankLine(),
    // Para 8: Roadmap
    bodyPara(
      'The remainder of this paper is organized as follows. Section 2 describes the data, ' +
      'features, model specifications, and backtesting design. Section 3 reports the ' +
      'empirical results across six subsections covering regime characterization, baseline ' +
      'performance, turnover analysis, implementation-aware variants, fixed-income ' +
      'expansion, and robustness checks. Section 4 discusses the findings in relation ' +
      'to data-driven macroeconomics, AI/machine-learning systems, systemic risk, and ' +
      'implementation-cost transparency. Section 5 concludes.'
    ),
    blankLine(),
  ];
}


// --- SECTION 2: MATERIALS AND METHODS ---
function buildSection2() {
  return [
    sectionHeading('2.', 'Materials and Methods'),
    subHeading('2.1.', 'Data and Asset Universe'),
    bodyPara(
      'The baseline investable universe consists of ten risky assets and one risk-free rate, ' +
      'all denominated in or converted to euros. The risky universe spans European equities ' +
      '(six indices: CAC 40, DAX, EuroStoxx 50, FTSE MIB, IBEX 35, and STOXX Europe 600), ' +
      'listed real estate (FTSE EPRA/NAREIT Europe), broad commodities (Bloomberg Commodity ' +
      'Index), energy (Brent crude oil front-month futures), and precious metals (gold spot, ' +
      'EUR-converted from USD). The risk-free instrument is the EURIBOR 3-month rate, used as ' +
      'the cash return benchmark and excluded from risky portfolio optimization. All series ' +
      'are sourced from LSEG Workspace (Refinitiv) as weekly Friday-close prices. Exceptions: ' +
      'Brent is a front-month futures price (RIC: LCOc1); gold is a USD spot price (XAU=) ' +
      'converted at weekly prevailing FX rates; and EURIBOR 3M (EUR3MD=) is a rate series ' +
      'converted to a weekly simple return. A 14-asset FI-expanded universe for robustness ' +
      'adds Germany, Spain, and Italy government bond total-return indices from FTSE Russell. ' +
      'Table 1 summarizes the complete universe.'
    ),
    blankLine(),
    bodyPara(
      'All series are aligned to weekly Friday-close observations over January 14, 2000 to ' +
      'April 3, 2026, yielding 1,369 weekly observations before burn-in exclusions. We use ' +
      'simple (arithmetic) weekly returns throughout; all strategy statistics are annualized ' +
      'using a factor of 52. Missing values from national holidays are forward-filled for up ' +
      'to five consecutive business days. Raw source files are subject to LSEG data licensing ' +
      'restrictions and cannot be distributed publicly; all results are reproducible from the ' +
      'processed parquet files accompanying this paper (see Data Availability Statement).'
    ),
    blankLine(),
    ...tblCaption(
      'Table 1',
      'Asset Universe',
      'The table reports the 11-asset baseline investable universe. RICs are LSEG Workspace ' +
      'identifiers. All return series are in EUR. TR = total return index. Brent crude oil and ' +
      'gold are price series, not total-return indices. EURIBOR 3M is excluded from the optimized ' +
      'risky portfolio. A 14-asset FI-expanded universe adds Germany, Spain, and Italy government ' +
      'bond TR indices from FTSE Russell; the Italy series (RIC .FTIT_TSYUSDT) is EUR-converted ' +
      'by LSEG.'
    ),
    buildTable1(),
    blankLine(),
    subHeading('2.2.', 'Macro-Financial Regime Features'),
    bodyPara(
      'The HMM is estimated on eight macro-financial features, each transformed to a 52-week ' +
      'rolling z-score to ensure comparable scale. The features are: VIX implied volatility ' +
      '(z52_VIX, primary anchor for state ordering); VSTOXX European implied volatility ' +
      '(z52_VSTOXX); MOVE fixed-income volatility index (z52_MOVE); Germany 10-year yield minus ' +
      'ECB deposit rate slope (z52_germany_10y_2y_slope); average sovereign spread of Spain, ' +
      'Portugal, and Italy over Germany (z52_peripheral_spread_avg); DXY dollar index ' +
      '(z52_DXY_USD_Index); Eurozone Economic Sentiment Indicator (z52_ESI, monthly, ' +
      'interpolated to weekly); and HICP headline-minus-core inflation gap ' +
      '(z52_hicp_headline_core_gap, approximately 4-week publication lag). Sample coverage ' +
      'ranges from 78% (ESI, HICP) to 100% (VIX). For a given week, the feature vector is ' +
      'constructed using the most recently available observation, with HICP subject to ' +
      'publication-lag risk (see Section 3.6).'
    ),
    blankLine(),
    bodyPara(
      'This feature set is designed to capture the primary macro-financial dimensions relevant ' +
      'to European multi-asset allocation: volatility and tail-risk sentiment (VIX, VSTOXX, MOVE), ' +
      'fixed-income market stress (sovereign spreads, yield-curve slope), macro growth and ' +
      'inflation pressure (ESI, HICP gap), and global risk appetite (DXY). Together these ' +
      'features encode the macro-financial information that historically differentiates ' +
      'crisis, recovery, expansion, and stress periods in European markets.'
    ),
    blankLine(),
    subHeading('2.3.', 'Hidden Markov Model Specification'),
    bodyPara(
      'We model the evolution of market states using a four-state Gaussian Hidden Markov Model ' +
      '(HMM; Hamilton, 1989; Rabiner, 1989; Kim, 1994) with diagonal covariance matrices, estimated via the Expectation-Maximization (EM) ' +
      'algorithm implemented in the hmmlearn library. We use 15 random restarts and up to 500 ' +
      'EM iterations per restart, selecting the solution with the highest log-likelihood. The ' +
      'four-state specification is selected by Bayesian Information Criterion (BIC) from a grid ' +
      'of two to five states; in all walk-forward windows, four states is consistently preferred. ' +
      'States are ordered post-estimation by ascending mean z52_VIX, so that State 0 has the ' +
      'lowest equity-volatility signature (Low-vol / Subdued) and State 3 the highest ' +
      '(Elevated-risk / Stress).'
    ),
    blankLine(),
    bodyPara(
      'All regime labels used in portfolio construction are strictly out-of-sample. We implement ' +
      'an expanding walk-forward procedure: at each four-week rebalance step, the HMM is ' +
      're-estimated from scratch on all available history up to the rebalance date, subject to ' +
      'a minimum of 156 weeks (three years) of training data. Panel B evaluation begins from ' +
      'October 15, 2010, to ensure stable four-state estimates. The walk-forward design ' +
      'contrasts with the partial in-sample evaluations common in earlier regime-switching ' +
      'portfolio work (Guidolin and Timmermann, 2007) and ensures that all reported performance ' +
      'metrics reflect genuine predictive content. Posterior state probabilities are soft ' +
      'assignments; the hard-assignment regime label is the argmax state at each week.'
    ),
    blankLine(),
    subHeading('2.4.', 'CVaR Portfolio Optimization'),
    bodyPara(
      'For a portfolio weight vector w, the Conditional Value-at-Risk (CVaR) at confidence ' +
      'level α = 0.95 is the expected loss conditional on being in the worst (1 - α) = 5% ' +
      'tail of the return distribution. CVaR is a coherent risk measure (Acerbi and Tasche, 2002) ' +
      'with superior tail-sensitivity relative to VaR-based approaches (Engle and Manganelli, 2004). ' +
      'Following Rockafellar and Uryasev (2000) and ' +
      'Krokhmal et al. (2002), CVaR is minimized via a linear program (LP) over a scenario ' +
      'set of T_s = 260 historical weekly returns. The LP takes the form:'
    ),
    blankLine(),
    ommlPara('__OMML_CVAR_OBJ__'),
    ommlPara('__OMML_CVAR_ST__'),
    blankLine(),
    bodyPara(
      'where ζ is the VaR threshold and u_t are auxiliary loss exceedance variables. ' +
      'The 25% maximum weight per asset prevents concentration risk. The scenario window ' +
      'is a rolling 260-week (5-year) history. We solve the LP using scipy.optimize.linprog ' +
      'at each four-week rebalance. As an additional benchmark, a Markowitz (1952) minimum-variance ' +
      'portfolio is estimated with a Ledoit-Wolf shrinkage covariance matrix (Ledoit and ' +
      'Wolf, 2004) and the same 25% weight cap.'
    ),
    blankLine(),
    subHeading('2.5.', 'Regime-Conditioned and Implementation-Aware Allocation Rules'),
    bodyPara(
      'We evaluate four allocation rules that use the HMM regime signal. Static CVaR uses all ' +
      '260 scenarios without regime conditioning and serves as the primary benchmark. ' +
      'Regime CVaR-A (naive conditioning) restricts the scenario set to historical weeks in ' +
      'which the current walk-forward regime label was active; if fewer than 30 such weeks ' +
      'are available, it falls back to the full 260-week window. Weighted CVaR assigns scenario ' +
      'weights proportional to the current week\'s HMM posterior, using all 260 scenarios.'
    ),
    blankLine(),
    bodyPara(
      'Two implementation-aware rules address the turnover friction. TC-aware CVaR augments ' +
      'the LP objective with an L1 turnover penalty: the modified objective is CVaR(w) + ' +
      'λ * Σ_i |w_i - w_{i,prev}|. A turnover-budget variant replaces the penalty with a ' +
      'hard bound: Σ_i |w_i - w_{i,prev}| <= τ. Both preserve LP linearity via auxiliary ' +
      'variables (see Appendix A). Regime-constrained CVaR uses the full 260-week scenario ' +
      'set but imposes regime-dependent group weight bounds on equity (six indices) and ' +
      'defensive assets (gold, Bloomberg Commodity, Brent): equity cap 45% and defensive ' +
      'floor 30% in Stress states; 75% equity cap and 10% floor in Risk-on states. ' +
      'This approach encodes investment policy beliefs as transparent guardrails without ' +
      'altering the scenario optimization problem.'
    ),
    blankLine(),
    subHeading('2.6.', 'Backtesting Design, Transaction Costs, and Statistical Inference'),
    bodyPara(
      'All strategies are rebalanced every four weeks. Panel A evaluates the long-horizon ' +
      'period from January 10, 2003 to April 3, 2026 (1,213 weeks) for non-regime strategies. ' +
      'Panel B evaluates from October 15, 2010 to April 3, 2026 (808 weeks) and includes ' +
      'all regime-conditioned strategies. Performance metrics include: annualized CAGR ' +
      '(weekly compounding, factor 52), annualized volatility (factor sqrt(52)), Sharpe ratio ' +
      '(mean excess return over EURIBOR 3M divided by standard deviation, times sqrt(52)), ' +
      'maximum drawdown (peak-to-trough on the cumulative wealth curve), 95% CVaR, ' +
      'Calmar ratio, and annualized turnover (mean weekly one-way turnover times 52). ' +
      'Transaction costs are modeled as TC_rate * Σ_i |w_{i,t} - w_{i,t-1}^+|, where ' +
      'w_{i,t-1}^+ is the post-drift pre-rebalance weight. We evaluate TC rates of 0, 5, ' +
      '10, and 25 basis points.'
    ),
    blankLine(),
    bodyPara(
      'We report two complementary statistical tests. First, a pairwise HAC/Newey-West ' +
      't-test (Newey and West, 1987) of mean excess-return differentials (strategy minus ' +
      'equal-weight benchmark) with lag = 13 weeks (one quarter). Second, a circular block-' +
      'bootstrap Sharpe confidence interval with block length 13 weeks and 5,000 draws, ' +
      'accounting for return autocorrelation without distributional assumptions. We caution ' +
      'that bootstrap intervals report individual strategy Sharpe uncertainty; they do not ' +
      'constitute pairwise Sharpe equality tests. Given 808 weekly observations and a 13-week ' +
      'HAC lag, effective degrees of freedom are substantially below nominal, and Sharpe ' +
      'differences of 0.1 to 0.2 cannot be conclusively attributed to skill versus sampling ' +
      'variation at conventional significance levels (Lo, 2002).'
    ),
    blankLine(),
    ...figCaption(
      'Figure 1',
      '',
      'Methodological workflow: from LSEG/Refinitiv raw data to mechanism diagnosis. HMM = Hidden Markov Model; CVaR = Conditional Value-at-Risk; TC = transaction cost; FI = fixed income; LP = linear program.'
    ),
    figImage(FIG.f1, 2181, 1440, 'Figure 1 Methodological Workflow'),
    blankLine(),
  ];
}

// Table-building functions (renamed from FINAL.js: buildTableI → buildTable1, etc.)
function buildTable1() {

  const cols = [2800, 1900, 1700, 2960];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const rows_data = [
    ['EURIBOR 3M',            'Risk-free proxy',     'EUR3MD=',     'Rate; weekly simple return; excluded from optimization'],
    ['Bloomberg Commodity',   'Commodity (broad)',   'BCOM',        'Total return index'],
    ['Brent Crude Oil',       'Energy',              'LCOc1',       'Front-month futures price'],
    ['Gold',                  'Precious metals',     'XAU=',        'USD spot; EUR-converted at weekly FX'],
    ['CAC 40',                'Equity (FR)',         '.FCHI',       'Total return'],
    ['DAX',                   'Equity (DE)',         '.GDAXI',      'Total return'],
    ['EuroStoxx 50',          'Equity (Eurozone)',   '.STOXX50E',   'Total return'],
    ['FTSE MIB',              'Equity (IT)',         '.FTMIB',      'Total return'],
    ['IBEX 35',               'Equity (ES)',         '.IBEX',       'Total return'],
    ['STOXX Europe 600',      'Equity (broad EU)',   '.STOXX',      'Total return; single-asset benchmark'],
    ['FTSE EPRA/NAREIT Europe','Listed real estate', '.FTEPRAEUR',  'Total return'],
  ];
  const hdrs = ['Asset', 'Type', 'RIC', 'Notes'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: AlignmentType.LEFT, width: cols[i], borders: hB, size: 20 })) }),
      ...rows_data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: AlignmentType.LEFT, width: cols[ci], borders: i === rows_data.length - 1 ? bB : mB, size: 20 })) })),
    ],
  });
}

// --- SECTION 3: RESULTS ---
function buildSection3() {
  return [
    sectionHeading('3.', 'Results'),
    subHeading('3.1.', 'Macro-Financial Regime Characterization'),
    bodyPara(
      'The four HMM states are ordered by ascending mean implied volatility z-score ' +
      '(z-VIX), yielding an economically intuitive volatility ladder: State 0 (Low-vol / ' +
      'Subdued) to State 3 (Elevated-risk / Stress). Figure 2 displays the mean 52-week ' +
      'z-scores of the four key macro-financial features across states; Table 2 provides ' +
      'full descriptive statistics. The state characteristics are consistent with recognizable ' +
      'European macro-financial episodes: State 1 (Risk-on / Expansion) captures broad ' +
      'growth phases, while State 3 identifies the Global Financial Crisis of 2008 to 2009, ' +
      'the European sovereign crisis of 2011 to 2012, and the COVID-19 crash of March 2020. ' +
      'These labels are interpretive, not model constraints; portfolio construction uses ' +
      'exclusively out-of-sample walk-forward labels (Figure 3).'
    ),
    blankLine(),
    ...tblCaption(
      'Table 2',
      'HMM Market-State Characteristics',
      'Four-state Gaussian HMM estimated on eight macro-financial z-score features (full-sample ' +
      'descriptive; portfolio construction uses strictly out-of-sample walk-forward labels). States ' +
      'ordered by ascending mean z52_VIX. Freq = share of weekly observations. Avg Dur = average ' +
      'episode duration (weeks). ESI = Economic Sentiment Indicator; Spread = average ES/PT/IT ' +
      'peripheral spread to Germany. HMM: Hidden Markov Model; VIX: CBOE Volatility Index.'
    ),
    buildTable2(),
    blankLine(),
    ...figCaption(
      'Figure 2',
      '',
      'Mean 52-week z-scores of key macro-financial features by HMM state (full-sample descriptive). States ordered by ascending z-VIX; colours match Figure 3.'
    ),
    figImage(FIG.f2s, 2200, 1000, 'Figure 2 HMM State Characteristics'),
    blankLine(),
    ...figCaption(
      'Figure 3',
      '',
      'Full-sample HMM regime timeline (2000 to 2026); in-sample labels for descriptive characterization only.'
    ),
    figImage(FIG.f3, 2096, 1408, 'Figure 3 Full-Sample Regime Timeline'),
    blankLine(),
    subHeading('3.2.', 'Static CVaR and Naive Regime Conditioning'),
    bodyPara(
      'Table 3 reports Panel A performance (1,213 weeks, 2003 to 2026). Static CVaR achieves ' +
      'the highest Sharpe ratio (0.513) and the lowest maximum drawdown (-39.5%) among all ' +
      'non-regime strategies, substantially better than the equal-weight (1/N) benchmark (DeMiguel et al., 2009) ' +
      '(-50.1%) and the STOXX Europe 600 single-asset benchmark (-60.2%). The risk reduction ' +
      'reflects the CVaR LP systematically concentrating in gold and Bloomberg Commodity ' +
      '(approximately 50% combined weight), which function as tail-risk dampeners in the ' +
      'absence of sovereign bonds. No strategy achieves a statistically significant ' +
      'excess-return differential over the equal-weight benchmark (HAC t-statistics below 1).'
    ),
    blankLine(),
    bodyPara(
      'Table 4 presents Panel B results (808 weeks, 2010 to 2026). Static CVaR remains the ' +
      'most robust benchmark with a Sharpe of 0.530. The naive Regime CVaR-A generates a ' +
      'gross Sharpe of only 0.365, and Weighted CVaR 0.368, both below the equal-weight ' +
      'benchmark (0.409). The underperformance is not attributable to poor regime detection ' +
      'but to the implementation friction documented in the next subsection.'
    ),
    blankLine(),
    ...tblCaption(
      'Table 3',
      'Panel A Performance: Long-Horizon Evaluation, 2003 to 2026',
      'Weekly simple returns, 1,213 observations (10 January 2003 to 3 April 2026). Gross ' +
      'performance at 0 bps transaction costs. Annualization factor 52. CAGR = compound annual ' +
      'growth rate. Vol = annualized standard deviation. Sharpe = (mean excess weekly return / ' +
      'SD excess) x sqrt(52) relative to EURIBOR 3M. MaxDD = maximum drawdown. CVaR 95% = ' +
      'average of worst 5% weekly returns. Ann. TO = annualized one-way portfolio turnover. ' +
      'Bootstrap 95% CI: circular block bootstrap, block = 13 weeks, 5,000 draws.'
    ),
    buildTable3(),
    blankLine(),
    ...tblCaption(
      'Table 4',
      'Panel B Performance: Regime-Aware Out-of-Sample Evaluation, 2010 to 2026',
      'Weekly simple returns, 808 observations (15 October 2010 to 3 April 2026). Gross ' +
      'performance at 0 bps transaction costs. HMM MIN_TRAIN_OBS = 156 weeks; all regime ' +
      'labels are strictly out-of-sample (walk-forward expanding window). Definitions as in ' +
      'Table 3. CVaR: Conditional Value-at-Risk; HMM: Hidden Markov Model.'
    ),
    buildTable4(),
    blankLine(),
    bodyPara(
      'Note on the Static CVaR Sharpe reference value: Table 4 reports Static CVaR at 0.530 ' +
      'gross Sharpe (808-week Panel B grid). Table 7, which reports implementation-aware ' +
      'experiments run on a different rebalance grid anchored from January 2000, reports ' +
      'Static CVaR at 0.553. The two values are both correct within their respective scopes: ' +
      'the 0.530 figure uses only rebalance dates that overlap with available HMM walk-forward ' +
      'labels (the label-intersected grid), while the 0.553 figure uses the full 2000-to-2026 ' +
      'rebalance grid and therefore covers a longer effective horizon. The difference of 0.023 ' +
      'reflects different sets of rebalance dates, not different empirical outcomes. All ' +
      'within-panel comparisons are internally consistent.'
    ),
    blankLine(),
    ...figCaption(
      'Figure 4',
      '',
      'Cumulative wealth of 1 EUR invested in October 2010 across all Panel B strategies at 0 bps transaction costs.'
    ),
    figImage(FIG.f4, 2511, 1220, 'Figure 4 Cumulative Wealth Panel B'),
    blankLine(),
    subHeading('3.3.', 'Turnover and the Transaction-Cost Channel'),
    bodyPara(
      'Table 5 reports the transaction-cost sensitivity of all strategies. Regime CVaR-A ' +
      'annual turnover is 225.8%, approximately 17.4% per four-week rebalance. Weighted CVaR ' +
      'is similar at 232.5%. By contrast, Static CVaR turns over only 21.4% annually. ' +
      'At 10 basis points of transaction cost, the net Sharpe of Regime CVaR-A falls to ' +
      '0.346, and Weighted CVaR to 0.348, compared to 0.528 for Static CVaR and 0.406 for ' +
      'Equal-Weight. At 25 bps the regime strategies register net Sharpe ratios of 0.317 ' +
      'and 0.318, respectively. The performance degradation is approximately linear in ' +
      'TC_rate times the turnover differential, confirming that turnover, not scenario ' +
      'filtering per se, is the dominant driver of net performance differences.'
    ),
    blankLine(),
    bodyPara(
      'This tenfold turnover differential arises because each regime transition causes the ' +
      'CVaR LP scenario set to change discontinuously, producing abrupt portfolio ' +
      'reconstitution at every state switch. Table 6 confirms that no pairwise ' +
      'HAC/Newey-West test achieves conventional significance: bootstrap Sharpe confidence ' +
      'intervals span approximately +-0.4 units for all strategies, so that point estimate ' +
      'differences of 0.1 to 0.2 cannot be conclusively attributed to skill versus ' +
      'sampling variation over the 808-week evaluation window.'
    ),
    blankLine(),
    ...tblCaption(
      'Table 5',
      'Transaction-Cost Sensitivity, Panel B (Net Sharpe Ratio)',
      'Net Sharpe ratios at four transaction-cost (TC) levels (0, 5, 10, 25 bps per ' +
      'one-way unit of turnover). Annual turnover reported at gross (TC = 0) level. ' +
      'TC is subtracted from gross weekly returns before computing Sharpe. CVaR: ' +
      'Conditional Value-at-Risk.'
    ),
    buildTable5(),
    blankLine(),
    ...tblCaption(
      'Table 6',
      'Statistical Tests, Panel B (2010 to 2026)',
      'Panel A: HAC/Newey-West one-sided t-test on weekly excess-return differentials ' +
      '(strategy minus Equal-Weight), Newey-West lag = 13 weeks. H_1: strategy mean ' +
      'excess return > benchmark. Panel B: Circular block-bootstrap 95% Sharpe ' +
      'confidence intervals, block = 13 weeks, 5,000 draws. Bootstrap CIs report ' +
      'individual strategy Sharpe uncertainty. No test achieves conventional significance. ' +
      'HAC: Heteroskedasticity and autocorrelation consistent.'
    ),
    buildTable6(),
    blankLine(),
    subHeading('3.4.', 'Implementation-Aware Regime Translation'),
    bodyPara(
      'Table 7 reports results for the two implementation-aware strategies. Panel A presents ' +
      'TC-aware CVaR specifications. The turnover-constrained specification at τ = 0.10 reduces ' +
      'Regime CVaR-A annual turnover from 225.8% to 59.9%, a reduction of 166 percentage points. ' +
      'Net Sharpe at 10 bps improves from 0.346 to 0.486. Despite these improvements, no ' +
      'TC-aware variant consistently surpasses Static CVaR (net Sharpe 0.551 at 10 bps in this ' +
      'experiment context; see Table 7 note for the scope difference relative to Table 4). ' +
      'The ZEW-swap penalized variant (ZEW+λ=0.005) produces an exploratory net Sharpe of ' +
      '0.567, which should not be interpreted as evidence of general outperformance: label ' +
      'agreement with the canonical HMM is only 47.9%, and this result is not confirmed in ' +
      'any other specification.'
    ),
    blankLine(),
    bodyPara(
      'Panel B of Table 7 presents regime-constrained CVaR results. This approach achieves ' +
      'near-static performance at 0.522 gross Sharpe (baseline HMM) and 0.519 (ZEW-swap HMM), ' +
      'with annual turnover of 29.2% and 27.0%, respectively, a substantial improvement over ' +
      'the 226% turnover of Regime CVaR-A. Net Sharpe at 10 bps reaches 0.519 and 0.517, ' +
      'within 0.009 of Static CVaR. This approach is also more transparent to a risk committee: ' +
      'it encodes a clear investment policy (reduce equity in stress, maintain defensive floor) ' +
      'rather than a less visible adjustment to the LP scenario set. Figure 5 illustrates the ' +
      'turnover versus net Sharpe frontier across all evaluated specifications.'
    ),
    blankLine(),
    bodyPara(
      'Table 7 uses experiment-specific rebalance grids and is intended for within-experiment ' +
      'comparison only. The Static CVaR row in Table 7 reflects the full 2000 to 2026 rebalance ' +
      'grid (Sharpe 0.553) and is not directly comparable to Table 4 (Sharpe 0.530, label-' +
      'intersected grid). The main Panel B benchmark for cross-strategy comparison remains Table 4.'
    ),
    blankLine(),
    ...tblCaption(
      'Table 7',
      'TC-Aware CVaR and Regime-Constrained CVaR: Selected Results',
      'Panel A: TC-aware CVaR with turnover budget (τ) and L1 penalty (λ). Panel B: Regime-' +
      'constrained CVaR with group-level weight bands varying by HMM state. Evaluation window: ' +
      '2010 to 2026, 808 weeks. ZEW-swap replaces z52_VSTOXX with z52_ZEW_Germany. Ann.TO = ' +
      'annualized one-way turnover. The ZEW+λ=0.005 result is exploratory (see text). Static ' +
      'CVaR in this table uses the full 2000-2026 rebalance grid (gross Sharpe 0.553 vs. 0.530 ' +
      'in Table 4 which uses the label-intersected grid; see Section 3.2 note). CVaR: ' +
      'Conditional Value-at-Risk; TC: transaction cost; HMM: Hidden Markov Model.'
    ),
    buildTable7(),
    blankLine(),
    ...figCaption(
      'Figure 5',
      '',
      'Turnover vs. net Sharpe frontier (Panel B, 10 bps) for all evaluated strategies and implementation-aware variants.'
    ),
    figImage(FIG.f5, 2198, 1310, 'Figure 5 Turnover vs Net Sharpe Frontier'),
    blankLine(),
    subHeading('3.5.', 'Sovereign Fixed-Income Expansion'),
    bodyPara(
      'Table 8 summarizes FI-expanded results. Panel A (2003 to 2026): adding three government ' +
      'bond total-return indices raises Static CVaR Sharpe from 0.513 to 0.547 (+0.034) while ' +
      'reducing maximum drawdown from -39.5% to -14.8% and annualized volatility from 12.2% to ' +
      '5.0%. The bond addition triggers a substantial allocation substitution: the CVaR LP ' +
      'reallocates approximately 73% of the portfolio to sovereign bonds, reducing equity to 3% ' +
      'and gold and commodities combined to 23.5%. This reflects the lower weekly CVaR of ' +
      'government bonds relative to equities and commodities, not a general recommendation ' +
      'to overweight bonds regardless of rate environment.'
    ),
    blankLine(),
    bodyPara(
      'Panel B (2010 to 2026): Static CVaR Sharpe declines slightly (-0.026) despite a ' +
      'material maximum drawdown improvement (-25.3% to -14.6%). The Sharpe decline is ' +
      'explained by the 2022 ECB rate-hiking cycle: with the FI-expanded portfolio holding ' +
      'approximately 75% in sovereign bonds entering 2022, the portfolio recorded losses of ' +
      'approximately -10% while the baseline portfolio held commodities and gold, which ' +
      'rose on energy inflation. This illustrates a key practical point: opportunity set design ' +
      'implicitly takes positions on macro risk factors, and the choice of whether to include ' +
      'fixed income constitutes an implicit bet on rate stability.'
    ),
    blankLine(),
    ...tblCaption(
      'Table 8',
      'FI-Expanded Universe: Performance Comparison',
      'Baseline = 11-asset universe. FI-Expanded = 14-asset universe adding Germany, Spain, ' +
      'and Italy government bond TR indices. Gross performance at 0 bps TC. Panel A: 2003 to ' +
      '2026. Panel B: 2010 to 2026. Delta = FI-Expanded minus Baseline. The 2022 ECB rate-' +
      'hiking episode was adverse for FI-expanded portfolios. FI: fixed income; TR: total return; ' +
      'TC: transaction cost.'
    ),
    buildTable8(),
    blankLine(),
    ...figCaption(
      'Figure 6',
      '',
      'Average asset-group weights of Static CVaR over Panel B (2010 to 2026), baseline vs. FI-expanded universe.'
    ),
    figImage(FIG.f6, 2211, 1160, 'Figure 6 Average Weights Baseline vs FI-Expanded'),
    blankLine(),
    ...figCaption(
      'Figure 7',
      '',
      'Drawdown curves for Static CVaR under the baseline and FI-expanded universes; the 2022 ECB rate-hiking cycle generates approximately -14.6% drawdown for the FI-expanded strategy.'
    ),
    figImage(FIG.f7, 2511, 1161, 'Figure 7 Drawdown Comparison Baseline vs FI-Expanded'),
    blankLine(),
    subHeading('3.6.', 'Robustness Checks'),
    bodyPara(
      'We conduct five robustness checks, summarized in Table 9. First, a 6-week HICP ' +
      'publication-lag correction addresses the risk that HICP data timestamps in LSEG ' +
      'reflect the reference period rather than the release date (approximately 17 days after ' +
      'month end). Label agreement between baseline and lagged specifications is approximately ' +
      '55%, confirming that HICP timing is a meaningful but not outcome-determining assumption. ' +
      'The Regime CVaR-A Sharpe changes by up to +0.068, within the bootstrap confidence band.'
    ),
    blankLine(),
    bodyPara(
      'Second, a ZEW feature swap replaces z52_VSTOXX with z52_ZEW_Germany (unconditional ' +
      'correlation with z52_ESI: r approximately 0.02). This improves Regime CVaR-A point ' +
      'estimates (Sharpe 0.365 to 0.483) but label agreement with the baseline is only 47.9%, ' +
      'and no test achieves statistical significance. These results are exploratory. Third, ' +
      'rebalance frequencies of 1, 2, 4, 8, and 13 weeks are tested; no frequency overturns ' +
      'Static CVaR as the most robust benchmark. Fourth, exponential weight averaging (EWA) ' +
      'blending reduces turnover approximately 30% and improves net Sharpe versus naive regime ' +
      'baseline, but does not surpass Static CVaR. Fifth, the FI-expanded universe robustness ' +
      'is reported in Section 3.5. Across all five checks, the main conclusion is unchanged.'
    ),
    blankLine(),
    ...tblCaption(
      'Table 9',
      'Robustness Check Summary',
      'All checks use the Panel B evaluation window (2010 to 2026, 808 weeks). Key metric ' +
      'is net Sharpe at 10 bps for Regime CVaR-A. Delta Sharpe = change vs. baseline. ' +
      'HICP: Harmonised Index of Consumer Prices; ZEW: Zentrum fuer Europaeische ' +
      'Wirtschaftsforschung; EWA: exponential weight averaging; CVaR: Conditional Value-at-Risk.'
    ),
    buildTable9(),
    blankLine(),
    subHeading('3.7.', 'Mechanism Summary'),
    bodyPara(
      'Table 10 synthesizes the six mechanisms through which naive regime-conditional CVaR ' +
      'underperforms the static benchmark, together with the implementation fix pursued in ' +
      'this paper and the remaining performance gap. The table serves as a diagnostic map ' +
      'connecting the theoretical mechanism (LP scenario discontinuity, estimation noise, ' +
      'hard label assignment, label sensitivity, macro-portfolio signal mismatch, and ' +
      'rate-shock exposure) to the empirical evidence and the practical resolution.'
    ),
    blankLine(),
    ...tblCaption(
      'Table 10',
      'Why Regime CVaR-A Fails: Mechanism Summary',
      'Six mechanisms linking regime detection to portfolio implementation failure. ' +
      'Empirical signatures refer to Panel B evaluation window (2010 to 2026, 808 weeks). ' +
      'Ann. TO = annualized one-way turnover. Net SR = net Sharpe at 10 bps. ' +
      'CVaR: Conditional Value-at-Risk; LP: linear program; HMM: Hidden Markov Model; ' +
      'HICP: Harmonised Index of Consumer Prices; ECB: European Central Bank.'
    ),
    buildTable10(),
    blankLine(),
  ];
}


function buildTable2() {
  const cols = [1400, 2200, 800, 900, 900, 900, 900, 760];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const hdrs = ['State', 'Label', 'Freq%', 'Avg Dur(w)', 'z52 VIX', 'z52 ESI', 'z52 Spread', 'z52 Slope'];
  const data = [
    ['0', 'Low-vol / Subdued',       '24.8', '13.3', '-0.96', '-0.33', '-0.31', '-1.31'],
    ['1', 'Risk-on / Expansion',     '28.5', '18.8', '-0.59', '+1.49', '-0.57', '+0.70'],
    ['2', 'Neutral / Moderate',      '26.9', '7.9',  '+0.05', '-0.73', '+0.15', '-0.36'],
    ['3', 'Elevated-risk / Stress',  '19.8', '7.2',  '+1.84', '-0.74', '+0.45', '+0.10'],
  ];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i <= 1 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      ...data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci <= 1 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: i === data.length - 1 ? bB : mB, size: 20 })) })),
    ],
  });
}

function buildTable3() {
  const cols = [2200, 1000, 900, 900, 900, 950, 950, 1360];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const data = [
    ['Equal-Weight Risky (1/N)', '5.89', '15.24', '0.368', '-50.1', '-5.24', '0.118', '36.3'],
    ['STOXX Europe 600',         '4.47', '17.50', '0.265', '-60.2', '-5.94', '0.074', '0.0'],
    ['Static CVaR',              '7.05', '12.22', '0.513', '-39.5', '-4.19', '0.179', '24.9'],
    ['Markowitz (Min-Var)',       '5.65', '12.02', '0.409', '-45.6', '-4.27', '0.124', '16.8'],
  ];
  const hdrs = ['Strategy', 'CAGR%', 'Vol%', 'Sharpe', 'MaxDD%', 'CVaR95%', 'Calmar', 'Ann.TO%'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      ...data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: i === data.length - 1 ? bB : mB, size: 20, bold: r[0] === 'Static CVaR' })) })),
    ],
  });
}

function buildTable4() {
  const cols = [2000, 900, 900, 900, 900, 900, 960];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const data = [
    ['Equal-Weight Risky (1/N)', '5.65', '14.43', '0.409', '-32.8', '-4.81', '35.2'],
    ['STOXX Europe 600',         '5.28', '15.86', '0.363', '-31.9', '-5.33',  '0.0'],
    ['Static CVaR',              '6.03', '10.97', '0.530', '-25.3', '-3.60', '21.4'],
    ['Markowitz (Min-Var)',       '5.03', '10.85', '0.447', '-24.9', '-3.64', '12.3'],
    ['Regime CVaR-A',            '4.35', '11.78', '0.365', '-25.8', '-3.96', '225.8'],
    ['Weighted CVaR',            '4.35', '11.62', '0.368', '-25.4', '-3.88', '232.5'],
  ];
  const hdrs = ['Strategy', 'CAGR%', 'Vol%', 'Sharpe', 'MaxDD%', 'CVaR95%', 'Ann.TO%'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      ...data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: i === data.length - 1 ? bB : mB, size: 20, bold: r[0] === 'Static CVaR' })) })),
    ],
  });
}

function buildTable5() {
  const cols = [2000, 900, 900, 900, 900, 960];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const data = [
    ['Equal-Weight Risky (1/N)', '0.409', '0.407', '0.406', '0.403', '35.2'],
    ['STOXX Europe 600',         '0.363', '0.363', '0.363', '0.363', '0.0'],
    ['Static CVaR',              '0.530', '0.529', '0.528', '0.525', '21.4'],
    ['Markowitz (Min-Var)',       '0.447', '0.446', '0.445', '0.444', '12.3'],
    ['Regime CVaR-A',            '0.365', '0.355', '0.346', '0.317', '225.8'],
    ['Weighted CVaR',            '0.368', '0.358', '0.348', '0.318', '232.5'],
  ];
  const hdrs = ['Strategy', '0 bps', '5 bps', '10 bps', '25 bps', 'Ann.TO%'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      ...data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: i === data.length - 1 ? bB : mB, size: 20, bold: r[0] === 'Static CVaR' })) })),
    ],
  });
}

function buildTable6() {
  // Fixed: row 4 Markowitz '-1.05%' (was math minus)
  const cols = [1900, 960, 900, 960, 500, 900, 800, 800];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const data = [
    ['Equal-Weight (1/N)',  '-',      '-',      '-',    '-', '0.409', '-0.054', '0.926'],
    ['STOXX Europe 600',   '-0.13%', '-0.096', '0.538', '',  '0.363', '-0.056', '0.833'],
    ['Static CVaR',        '-0.09%', '-0.059', '0.523', '',  '0.530', '+0.068', '1.058'],
    ['Markowitz (Min-Var)','-1.05%', '-0.682', '0.752', '',  '0.447', '-0.004', '0.962'],
    ['Regime CVaR-A',      '-1.60%', '-1.227', '0.890', '',  '0.365', '-0.079', '0.880'],
    ['Weighted CVaR',      '-1.62%', '-1.193', '0.883', '',  '0.368', '-0.074', '0.891'],
  ];
  const hdrs = ['Strategy', 'Ann.Diff', 't-stat', 'p(1-sided)', 'Sig', 'Sharpe', 'CI Lo', 'CI Hi'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      ...data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: i === data.length - 1 ? bB : mB, size: 20, bold: r[0] === 'Static CVaR' })) })),
    ],
  });
}

function buildTable7() {
  const cols = [2500, 1000, 950, 950, 3160];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const pB = { top: TB,  bottom: TNB, left: TNB, right: TNB };

  const panelRow = (text, isFirst) => new TableRow({
    children: [tcell(text, { colspan: 5, align: AlignmentType.LEFT, width: CONTENT, borders: isFirst ? pB : { top: TB, bottom: TNB, left: TNB, right: TNB }, bold: true, size: 20 })],
  });
  const mkRow = (r, isLast) => new TableRow({
    children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: isLast ? bB : mB, size: 20 })),
  });

  const hdrs = ['Strategy', 'Gross Sharpe', 'Net @10bps', 'Ann.TO%', ''];
  const dataA = [
    ['Static CVaR, experiment-grid benchmark',  '0.553', '0.551', '20.6%', ''],
    ['Regime CVaR-A, unconstrained',       '0.365', '0.346', '225.8%', ''],
    ['Regime CVaR-A, τ=0.10',         '0.491', '0.486', '59.9%', ''],
    ['Regime CVaR-A, τ=0.20',         '0.449', '0.440', '101.2%', ''],
    ['Weighted CVaR, τ=0.10',         '0.492', '0.486', '61.5%', ''],
    ['Weighted CVaR, ZEW+λ=0.005*',   '0.572', '0.567', '64.8%', '*Exploratory'],
  ];
  const dataB = [
    ['Static CVaR, experiment-grid benchmark',  '0.553', '0.551', '20.6%', ''],
    ['Regime-Constrained CVaR (baseline HMM)',  '0.522', '0.519', '29.2%', ''],
    ['Regime-Constrained CVaR (ZEW-swap HMM)', '0.519', '0.517', '27.0%', ''],
    ['Regime CVaR-A (baseline, for reference)', '0.365', '0.346', '225.8%', ''],
  ];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      panelRow('Panel A: TC-Aware CVaR', true),
      ...dataA.map((r, i) => mkRow(r, false)),
      panelRow('Panel B: Regime-Constrained CVaR (Weight-Band Approach)', false),
      ...dataB.map((r, i) => mkRow(r, i === dataB.length - 1)),
    ],
  });
}

function buildTable8() {
  const cols = [2000, 900, 900, 900, 900, 900, 960];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const pB = { top: TB,  bottom: TNB, left: TNB, right: TNB };

  const panelRow = (text, isFirst) => new TableRow({
    children: [tcell(text, { colspan: 7, align: AlignmentType.LEFT, width: CONTENT, borders: isFirst ? pB : { top: TB, bottom: TNB, left: TNB, right: TNB }, bold: true, size: 20 })],
  });
  const hdrs = ['Strategy', 'Sharpe Base', 'Sharpe FI-Exp', 'Delta Sharpe', 'MaxDD Base', 'MaxDD FI-Exp', 'Delta MaxDD'];
  const dataA = [
    ['Equal-Weight Risky', '0.368', '0.313', '-0.055', '-50.1%', '-38.9%', '+11.2pp'],
    ['Static CVaR',        '0.513', '0.547', '+0.034', '-39.5%', '-14.8%', '+24.7pp'],
    ['Markowitz (Min-Var)','0.409', '0.447', '+0.038', '-45.6%', '-14.2%', '+31.4pp'],
  ];
  const dataB = [
    ['Static CVaR',        '0.530', '0.504', '-0.026', '-25.3%', '-14.6%', '+10.7pp'],
    ['Markowitz (Min-Var)','0.447', '0.463', '+0.016', '-24.9%', '-14.4%', '+10.5pp'],
    ['Regime CVaR-A',      '0.365', '0.430', '+0.065', '-25.8%', '-17.2%', '+8.6pp'],
    ['Weighted CVaR',      '0.368', '0.378', '+0.010', '-25.4%', '-16.3%', '+9.1pp'],
  ];
  const mkRow = (r, isLast) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[ci], borders: isLast ? bB : mB, size: 20 })) });
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: cols[i], borders: hB, size: 20 })) }),
      panelRow('Panel A: 2003 to 2026', true),
      ...dataA.map((r, i) => mkRow(r, false)),
      panelRow('Panel B: 2010 to 2026', false),
      ...dataB.map((r, i) => mkRow(r, i === dataB.length - 1)),
    ],
  });
}

function buildTable9() {
  // Table IX: smaller font (18pt), allows text wrapping
  const cols = [1700, 2900, 1600, 3160];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const data = [
    ['HICP lag 6 weeks',
     'Label agreement ~55%; Regime CVaR-A Sharpe changes up to +0.068',
     'Within bootstrap noise',
     'Unchanged'],
    ['ZEW feature swap',
     'Regime CVaR-A Sharpe: 0.365 to 0.483 (+0.118); label agreement 47.9%; exploratory',
     'No test significant',
     'Unchanged'],
    ['Rebalance frequency',
     'Lower frequency reduces turnover; 4-week baseline reasonable',
     'No cadence overturns Static CVaR',
     'Unchanged'],
    ['Turnover smoothing (EWA)',
     'EWA blending reduces turnover ~30%; improves net Sharpe vs. naive regime',
     'Does not surpass Static CVaR',
     'Unchanged'],
    ['FI-expanded universe',
     'Panel A Sharpe +0.034; Panel B -0.026; MaxDD improved in both panels; 2022 rate-shock adverse',
     '-10% to -13% portfolio loss in 2022',
     'Unchanged'],
  ];
  const hdrs = ['Check', 'Key Finding', 'Magnitude', 'Conclusion'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: AlignmentType.LEFT, width: cols[i], borders: hB, size: 18 })) }),
      ...data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: AlignmentType.LEFT, width: cols[ci], borders: i === data.length - 1 ? bB : mB, size: 18 })) })),
    ],
  });
}

function buildTable10() {
  const cols = [2200, 1800, 1700, 1800, 1860];
  const hB = { top: TBT, bottom: TB,  left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const rows_data = [
    [
      'LP scenario discontinuity',
      'Regime switch replaces entire 260-scenario set with 30-80 matched scenarios',
      '226% annual turnover; tenfold vs. static benchmark',
      'L1 turnover penalty in LP objective reduces TO to 60%',
      'Net SR 0.486 vs. 0.528 for Static CVaR',
    ],
    [
      'Small scenario set',
      'CVaR tail estimated from handful of regime-matched observations',
      'Higher OOS estimation error; lower gross Sharpe (0.365 vs. 0.530)',
      'Regime constraints retain full 260-scenario set',
      'Net SR 0.519 vs. 0.528; not statistically significant',
    ],
    [
      'Hard label assignment',
      'Argmax discards posterior uncertainty (e.g., 40% / 35% / 25% spread)',
      'Weighted CVaR soft-weights scenarios but still underperforms static',
      'Soft-weighting (Weighted CVaR) partially addresses uncertainty',
      'No improvement over static in any specification',
    ],
    [
      'Label sensitivity',
      'HICP-lag6: 55% label agreement; ZEW swap: 47.9% label agreement with baseline',
      'Robustness Sharpe spread <0.02; conclusions unchanged',
      'Feature robustness checks (ZEW swap, HICP lag)',
      'No dominant feature set identified',
    ],
    [
      'Macro-portfolio mismatch',
      'Regime signal estimated on macro features; traded assets are financial returns',
      'No asset-level signal decomposition possible with current design',
      'Factor-orthogonal HMM design (not pursued in this paper)',
      'Open research question',
    ],
    [
      'Rate-shock exposure (FI)',
      'Bond inclusion changes risk factor profile toward duration',
      '-10% to -13% FI-expanded portfolio losses in 2022 ECB cycle',
      'Explicit duration constraint on bond allocation',
      'Not pursued; opportunity-set design trade-off',
    ],
  ];
  const hdrs = ['Mechanism', 'Root Cause', 'Empirical Signature', 'Implementation Fix', 'Remaining Gap'];
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({ tableHeader: true, children: hdrs.map((h, i) => tcell(h, { bold: true, align: AlignmentType.LEFT, width: cols[i], borders: hB, size: 20 })) }),
      ...rows_data.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: AlignmentType.LEFT, width: cols[ci], borders: i === rows_data.length - 1 ? bB : mB, size: 20 })) })),
    ],
  });
}

// --- SECTION 4: DISCUSSION ---
function buildSection4() {
  return [
    sectionHeading('4.', 'Discussion'),
    subHeading('4.1.', 'Implications for Next-Generation Macro-Financial Systems'),
    bodyPara(
      'This result is directly relevant to the Special Issue theme of next-generation data-' +
      'driven macroeconomic systems: the bottleneck is not forecasting or state detection, ' +
      'but the design of transparent and implementable decision rules. An AI or machine-' +
      'learning system that accurately identifies macro-financial regimes but translates ' +
      'those labels via naive scenario filtering will systematically underperform a simpler ' +
      'static optimizer due to implementation friction (Gu et al., 2020; Campbell and ' +
      'Viceira, 2002). The European context studied here, spanning the GFC, the sovereign ' +
      'debt crisis, the COVID shock, and the 2022 rate-hiking cycle, provides a stringent ' +
      'real-world test of this principle: detection works, but naive implementation does not.'
    ),
    blankLine(),
    bodyPara(
      'The HMM states identified here map onto recognizable European macro-financial episodes ' +
      'and are consistent across walk-forward windows, offering interpretability that black-' +
      'box detectors cannot provide. For systemic risk monitoring, the stress state (State 3) ' +
      'identifies periods of elevated sovereign spread widening, VIX spikes, and deteriorating ' +
      'sentiment, subject to the caveat that state assignments are sensitive to feature ' +
      'construction choices. Three structural mechanisms explain the failure of naive regime ' +
      'conditioning to improve performance. First, restricting to 30 to 80 regime-matched ' +
      'scenarios replaces a well-conditioned optimization with a fragile problem based on a ' +
      'small, historically idiosyncratic sample; estimation error propagates directly to ' +
      'higher turnover. Second, regime transitions cause the entire CVaR scenario set to ' +
      'change discontinuously at each rebalance, generating portfolio reconstitution that is ' +
      'not compensated by return improvements. Third, HMM posteriors are often diffuse in ' +
      'moderate conditions: the hard argmax assignment discards this uncertainty, and even ' +
      'soft-weighted CVaR fails to recover performance, indicating that signal content, not ' +
      'assignment rule, is the binding constraint.'
    ),
    blankLine(),
    subHeading('4.2.', 'Implications for Practice and Sovereign Risk Management'),
    bodyPara(
      'The regime-constraints approach is the most practically viable regime-aware mechanism ' +
      'identified in this study. By encoding investment policy beliefs as group-level weight ' +
      'guardrails while keeping the full CVaR scenario set intact, it achieves near-static ' +
      'performance at moderate turnover and produces a policy that can be audited by a risk ' +
      'committee. This approach aligns with how institutional investors use macro views in ' +
      'practice: as overlays on allocation rather than wholesale replacements of the ' +
      'optimization framework. The regime-constrained design also generates more stable ' +
      'portfolio sequences over time, reducing operational complexity and capacity constraints ' +
      'that would otherwise further reduce the gross performance advantage of regime-conditioned ' +
      'strategies at scale.'
    ),
    blankLine(),
    bodyPara(
      'The FI-expanded results highlight a second practical implication related to sovereign ' +
      'risk and interest-rate sensitivity. When sovereign bonds are unavailable, the CVaR ' +
      'optimizer concentrates in commodities and gold, which provided effective hedges in the ' +
      '2022 inflationary episode but performed poorly in the 2008 initial phase of the GFC. ' +
      'Adding bonds produces a more conventional allocation but introduces duration risk that ' +
      'materializes in rate-hiking cycles. Practitioners should be explicit about which macro ' +
      'risk factors their opportunity-set design is implicitly accepting, particularly in ' +
      'a European context where ECB policy and peripheral sovereign spread dynamics create ' +
      'risk exposures absent in typical US-centric frameworks.'
    ),
    blankLine(),
    bodyPara(
      'A related implication concerns the choice of evaluation benchmark. Static CVaR is a ' +
      'disciplined, systematic strategy with strong risk-control properties; it represents a ' +
      'genuinely demanding bar. Practitioners comparing regime-conditioned CVaR to a 60/40 ' +
      'portfolio or an equal-weight benchmark may reach more favorable conclusions, but such ' +
      'comparisons conflate the value of the CVaR optimization framework with the incremental ' +
      'value of regime conditioning, making performance attribution ambiguous.'
    ),
    blankLine(),
    subHeading('4.3.', 'Limitations'),
    bodyPara(
      'HMM regime labels are statistical constructs, not causal economic states. The model ' +
      'identifies recurring distributional patterns in the feature vector that need not ' +
      'correspond to structurally distinct regimes in any fundamental sense. The 55% label ' +
      'agreement between baseline and HICP-lagged specifications, and the 47.9% agreement ' +
      'with the ZEW feature swap, suggest that regime assignments are sensitive to feature ' +
      'construction choices in ways that likely reflect measurement uncertainty rather than ' +
      'genuine economic state differences. All downstream portfolio conclusions inherit ' +
      'this uncertainty.'
    ),
    blankLine(),
    bodyPara(
      'Feature sensitivity is a material concern. The ZEW-swap specification has only 47.9% ' +
      'label agreement with the baseline HMM, indicating that swapping a single feature ' +
      'substantially reorganises the regime classification. Regime assignments are sensitive ' +
      'to feature construction choices in ways that likely reflect measurement uncertainty ' +
      'rather than genuine economic state differences. Macro release timing ' +
      'introduces potential look-ahead risk for HICP (approximately 4-week publication lag) ' +
      'and ESI (approximately 3-week lag); the HICP-lag6 robustness check addresses HICP ' +
      'specifically, but ESI publication lag is not separately corrected. Practitioners ' +
      'implementing this design should apply publication-lag buffers to all macro features.'
    ),
    blankLine(),
    bodyPara(
      'The transaction-cost model is simplified: 10 bps one-way covers a range of ' +
      'institutional scenarios but does not model bid-ask spreads on futures contracts, ' +
      'market impact for large trades, or the operational costs of frequent rebalancing. ' +
      'The asset universe excludes corporate credit and inflation-linked bonds, which would ' +
      'add additional dimensions to the diversification and TC modeling. Raw LSEG source ' +
      'data are proprietary. Results are out-of-sample within the 2000 to 2026 European ' +
      'sample but remain sample-specific; generalization to other geographic markets or ' +
      'time periods requires further validation.'
    ),
    blankLine(),
    bodyPara(
      'Statistical power is a binding constraint. With 808 weekly observations and a ' +
      'Newey-West HAC lag of 13 weeks, effective degrees of freedom are substantially ' +
      'below nominal. Bootstrap confidence intervals for Sharpe ratios span approximately ' +
      '+-0.4 units, meaning point estimate differences of 0.1 to 0.2 cannot be ' +
      'conclusively attributed to regime-conditioning skill versus sampling variation. ' +
      'The failure to detect statistically significant outperformance is consistent with ' +
      'both "regime conditioning adds no value" and "the sample is too short to detect ' +
      'realistic Sharpe differences at conventional power." A longer or geographically ' +
      'diversified replication would sharpen these inferences.'
    ),
    blankLine(),
  ];
}

// --- SECTION 5: CONCLUSIONS ---
function buildSection5() {
  return [
    sectionHeading('5.', 'Conclusions'),
    bodyPara(
      'This paper shows that, in data-driven macro-financial systems, the binding constraint ' +
      'is not regime detection but decision-rule design. A four-state Gaussian HMM estimated ' +
      'on eight weekly macro-financial features produces economically interpretable, auditable ' +
      'states over a 26-year European sample, but naive translation of those states into ' +
      'CVaR portfolio allocation fails: regime-conditional scenario filtering generates annual ' +
      'turnover of 226%, eroding net performance below the equal-weight benchmark at any ' +
      'realistic transaction cost.'
    ),
    blankLine(),
    bodyPara(
      'Implementation-aware design substantially closes the gap. Regime-constrained weight ' +
      'bands achieve a net Sharpe of 0.519 at 29% annual turnover, within 0.009 of the ' +
      'static CVaR benchmark (0.530 gross Sharpe) at a fraction of the rebalancing cost. ' +
      'Expanding the universe to include sovereign bonds improves drawdown control but ' +
      'introduces duration risk that materializes sharply in rate-hiking episodes. Opportunity-' +
      'set design is itself an implicit macro bet and must be treated as such.'
    ),
    blankLine(),
    bodyPara(
      'These findings provide a practical blueprint for next-generation AI-assisted allocation ' +
      'frameworks: regime classifiers should be evaluated not only on detection accuracy but ' +
      'on the cost-efficiency and stability of the decision layer they enable. Future research ' +
      'should explore ensemble regime detectors, richer feature engineering, and replication ' +
      'in non-European markets to assess generalizability.'
    ),
    blankLine(),
  ];
}

// --- REFERENCES (MDPI author-date, alphabetical) ---
function buildReferences() {
  const refs = [
    'Acerbi, C., and Tasche, D. (2002). On the coherence of expected shortfall. Journal of Banking and Finance, 26, 1487-1503. https://doi.org/10.1016/S0378-4266(02)00283-2',
    'Adrian, T., and Brunnermeier, M. K. (2016). CoVaR. American Economic Review, 106, 1705-1741. https://doi.org/10.1257/aer.20120555',
    'Ang, A., and Bekaert, G. (2002). International asset allocation with regime shifts. Review of Financial Studies, 15, 1137-1187. https://doi.org/10.1093/rfs/15.4.1137',
    'Ang, A., and Bekaert, G. (2004). How regimes affect asset allocation. Financial Analysts Journal, 60, 86-99. https://doi.org/10.2469/faj.v60.n2.2612',
    'Bernanke, B. S., and Boivin, J. (2003). Monetary policy in a data-rich environment. Journal of Monetary Economics, 50, 525-546. https://doi.org/10.1016/S0304-3932(03)00024-2',
    'Billio, M., Getmansky, M., Lo, A. W., and Pelizzon, L. (2012). Econometric measures of connectedness and systemic risk in the finance and insurance sectors. Journal of Financial Economics, 104, 535-559. https://doi.org/10.1016/j.jfineco.2011.12.010',
    'Black, F., and Litterman, R. (1992). Global portfolio optimization. Financial Analysts Journal, 48, 28-43. https://doi.org/10.2469/faj.v48.n5.28',
    'Campbell, J. Y., and Viceira, L. M. (2002). Strategic Asset Allocation: Portfolio Choice for Long-Term Investors. Oxford University Press. https://doi.org/10.1093/0198296940.001.0001',
    'DeMiguel, V., Garlappi, L., and Uppal, R. (2009). Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy? Review of Financial Studies, 22, 1915-1953. https://doi.org/10.1093/rfs/hhm075',
    'Engle, R. F., and Manganelli, S. (2004). CAViaR: Conditional autoregressive value at risk by regression quantiles. Journal of Business and Economic Statistics, 22, 367-381. https://doi.org/10.1198/073500104000000370',
    'Frazzini, A., Israel, R., and Moskowitz, T. J. (2015). Trading costs of asset pricing anomalies. Working Paper, AQR Capital Management. Available at SSRN: https://ssrn.com/abstract=2294498',
    'Guidolin, M., and Timmermann, A. (2007). Asset allocation under multivariate regime switching. Journal of Economic Dynamics and Control, 31, 3503-3544. https://doi.org/10.1016/j.jedc.2006.11.007',
    'Gu, S., Kelly, B., and Xiu, D. (2020). Empirical asset pricing via machine learning. Review of Financial Studies, 33, 2223-2273. https://doi.org/10.1093/rfs/hhaa009',
    'Hamilton, J. D. (1989). A new approach to the economic analysis of nonstationary time series and the business cycle. Econometrica, 57, 357-384. https://doi.org/10.2307/1912559',
    'Kim, C.-J. (1994). Dynamic linear models with Markov-switching. Journal of Econometrics, 60, 1-22. https://doi.org/10.1016/0304-4076(94)90036-1',
    'Krokhmal, P., Palmquist, J., and Uryasev, S. (2002). Portfolio optimization with conditional value-at-risk objective and constraints. Journal of Risk, 4, 43-68. https://doi.org/10.21314/JOR.2002.057',
    'Ledoit, O., and Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. Journal of Multivariate Analysis, 88, 365-411. https://doi.org/10.1016/S0047-259X(03)00096-4',
    'Lo, A. W. (2002). The statistics of Sharpe ratios. Financial Analysts Journal, 58, 36-52. https://doi.org/10.2469/faj.v58.n4.2453',
    'Longin, F., and Solnik, B. (2001). Extreme correlation of international equity markets. Journal of Finance, 56, 649-676. https://doi.org/10.1111/0022-1082.00340',
    'Markowitz, H. (1952). Portfolio selection. Journal of Finance, 7, 77-91. https://doi.org/10.2307/2975974',
    'Newey, W., and West, K. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica, 55, 703-708. https://doi.org/10.2307/1913610',
    'Novy-Marx, R., and Velikov, M. (2016). A taxonomy of anomalies and their trading costs. Review of Financial Studies, 29, 104-147. https://doi.org/10.1093/rfs/hhv063',
    'Rabiner, L. R. (1989). A tutorial on hidden Markov models and selected applications in speech recognition. Proceedings of the IEEE, 77, 257-286. https://doi.org/10.1109/5.18626',
    'Rockafellar, R. T., and Uryasev, S. (2000). Optimization of conditional value-at-risk. Journal of Risk, 2, 21-41. https://doi.org/10.21314/JOR.2000.038',
  ];
  return [
    sectionHeading('', 'References'),
    ...refs.map(r => new Paragraph({
      children: [run(r, { size: 18 })],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 60, line: 280, lineRule: 'atLeast' },
      indent: { left: BODY_INDENT + 360, hanging: 360 },
    })),
    blankLine(),
  ];
}



// --- MDPI BACK MATTER ---
function buildBackMatter(blinded = false) {
  const smPara = (text, bold_prefix = '') => new Paragraph({
    children: bold_prefix
      ? [run(bold_prefix, { bold: true, size: 22 }), run(text, { size: 22 })]
      : [run(text, { size: 22 })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 60, after: 60, line: 360, lineRule: 'auto' },
  });
  const smHead = (title) => new Paragraph({
    children: [run(title, { bold: true, size: 22 })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 240, after: 60, line: 360, lineRule: 'auto' },
  });
  return [
    pageBreakPara(),
    smHead('Supplementary Materials:'),
    smPara(
      'The following supporting materials can be made available upon request or deposited ' +
      'as supplementary files, subject to LSEG/Refinitiv licensing restrictions: Python scripts ' +
      '(data pipeline, HMM estimation, CVaR LP, backtesting), processed weekly return and ' +
      'regime label parquet files, robustness tables, and figure-generation scripts. Raw ' +
      'LSEG/Refinitiv source files cannot be redistributed.'
    ),
    blankLine(),
    smHead('Author Contributions:'),
    ...(blinded
      ? [smPara('[Removed for peer review]')]
      : [smPara(
          'Conceptualization, J.G.; methodology, J.G.; software, J.G.; validation, J.G.; ' +
          'formal analysis, J.G.; investigation, J.G.; data curation, J.G.; writing, original ' +
          'draft preparation, J.G.; writing, review and editing, J.G.; visualization, J.G.; ' +
          'project administration, J.G. The author has read and agreed to the published version ' +
          'of the manuscript.'
        )]
    ),
    blankLine(),
    smHead('Funding:'),
    smPara('This research received no external funding.'),
    blankLine(),
    smHead('Institutional Review Board Statement:'),
    smPara('Not applicable.'),
    blankLine(),
    smHead('Informed Consent Statement:'),
    smPara('Not applicable.'),
    blankLine(),
    smHead('Data Availability Statement:'),
    smPara(
      'Restrictions apply to the availability of the raw data. The data were obtained from ' +
      'LSEG Workspace/Refinitiv and are available from LSEG subject to license. Processed ' +
      'datasets and code sufficient to reproduce the reported tables and figures can be made ' +
      'available by the author upon reasonable request, subject to licensing restrictions.'
    ),
    blankLine(),
    smHead('Acknowledgments:'),
    ...(blinded
      ? [smPara('[Removed for peer review]')]
      : [smPara('The author thanks colleagues and academic supervisors for helpful comments and feedback on earlier drafts of this work. '),
         smPara(
           'AI Tools Disclosure: During the preparation of this manuscript, the author used ' +
           'ChatGPT (OpenAI) and Claude (Anthropic) for language editing, code review, ' +
           'document formatting support, and research workflow assistance. The author reviewed ' +
           'and edited all AI-assisted outputs and takes full responsibility for the content ' +
           'of the publication.'
         )]
    ),
    blankLine(),
    smHead('Conflicts of Interest:'),
    smPara('The author declares no conflicts of interest.'),
    blankLine(),
    smHead('Abbreviations:'),
    smPara('The following abbreviations are used in this manuscript:'),
    blankLine(),
    ...[
      ['CVaR', 'Conditional Value-at-Risk'],
      ['HMM', 'Hidden Markov Model'],
      ['ESI', 'Economic Sentiment Indicator (Eurozone)'],
      ['HICP', 'Harmonised Index of Consumer Prices'],
      ['HAC', 'Heteroskedasticity and autocorrelation consistent'],
      ['TC', 'Transaction cost'],
      ['ECB', 'European Central Bank'],
      ['FI', 'Fixed income'],
      ['VIX', 'CBOE Volatility Index'],
      ['GFC', 'Global Financial Crisis'],
      ['LP', 'Linear program'],
      ['BIC', 'Bayesian Information Criterion'],
      ['EM', 'Expectation-Maximization'],
      ['OOS', 'Out-of-sample'],
      ['LSEG', 'London Stock Exchange Group'],
    ].map(([abbr, def]) => new Paragraph({
      children: [
        run(abbr + ': ', { bold: true, size: 22 }),
        run(def, { size: 22 }),
      ],
      spacing: { before: 30, after: 30, line: 300, lineRule: 'auto' },
    })),
    blankLine(),
  ];
}

// --- APPENDICES ---
function buildAppendices() {
  const appCTblCols = [2000, 1800, 2000, 3560];
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };
  const appCData = [
    ['0', 'Low-vol / Subdued',      '65%', '15%'],
    ['1', 'Risk-on / Expansion',    '75%', '10%'],
    ['2', 'Neutral / Moderate',     '60%', '15%'],
    ['3', 'Elevated-risk / Stress', '45%', '30%'],
  ];
  const appCHdrs = ['State', 'Label', 'Max Equity (sum)', 'Min Defensive (sum)'];
  const appCTbl = new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: appCTblCols,
    rows: [
      new TableRow({ tableHeader: true, children: appCHdrs.map((h, i) => tcell(h, { bold: true, align: i <= 1 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: appCTblCols[i], borders: hB, size: 20 })) }),
      ...appCData.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci <= 1 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: appCTblCols[ci], borders: i === appCData.length - 1 ? bB : mB, size: 20 })) })),
    ],
  });

  return [
    pageBreakPara(),
    new Paragraph({ children: [run('APPENDIX')], alignment: AlignmentType.CENTER, spacing: { before: 0, after: 240, line: 480, lineRule: 'auto' } }),
    new Paragraph({ children: [run('Appendix A: CVaR LP Formulation with Transaction Costs', { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 120, after: 240, line: 480, lineRule: 'auto' } }),
    bodyPara(
      'The TC-aware CVaR LP is formulated as follows. Let w^prev denote the portfolio weights after ' +
      'drift from the previous rebalance, before trading. Define auxiliary variables v_i^+ = max(w_i ' +
      '- w_i^prev, 0) and v_i^- = max(w_i^prev - w_i, 0). The L1 turnover is sum_i (v_i^+ + v_i^-). ' +
      'The penalized LP minimizes:'
    ),
    blankLine(),
    eqPara('__OMML_EQ1__: min  CVaR(w) + λ · Σᵢ (vᵢ⁺ + vᵢ⁻)'),
    eqPara('__OMML_EQ2__: s.t.  wᵢ − wᵢᵖʳᵉᵛ = vᵢ⁺ − vᵢ⁻,  vᵢ⁺, vᵢ⁻ ≥ 0'),
    blankLine(),
    bodyPara(
      'plus the standard CVaR constraints (see Section 2.4). The constrained formulation replaces ' +
      'the penalty term with a hard bound: sum_i (v_i^+ + v_i^-) <= τ. Both are linear in all ' +
      'decision variables and implementable with scipy.optimize.linprog.'
    ),
    blankLine(),
    new Paragraph({ children: [run('Appendix B: HMM Feature Construction', { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240, line: 480, lineRule: 'auto' } }),
    bodyPara(
      'All eight HMM features are computed as 52-week rolling z-scores of their underlying ' +
      'macro-financial time series. For a series x_t, the z-score at week t is z_t = (x_t - ' +
      'mu_{t,52}) / sigma_{t,52}, where mu and sigma are the sample mean and standard deviation ' +
      'of the preceding 52 weeks (excluding the current observation). Features with fewer than ' +
      '52 observations of history receive a NaN assignment and are excluded from that week\'s ' +
      'training sample.'
    ),
    blankLine(),
    new Paragraph({ children: [run('Appendix C: Regime-Constrained CVaR, Constraint Map', { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240, line: 480, lineRule: 'auto' } }),
    bodyPara(
      'Equity assets are the six European equity indices. Defensive assets are gold, Bloomberg ' +
      'Commodity Index, and Brent crude oil. The regime-specific constraint bands are as follows:'
    ),
    blankLine(),
    appCTbl,
    blankLine(),
    new Paragraph({ children: [run('Appendix D: Data Sources and Series Details', { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240, line: 480, lineRule: 'auto' } }),
    bodyPara(
      'All price series are sourced from LSEG Workspace (Refinitiv) as weekly Friday-close values ' +
      'unless noted. EURIBOR 3M is sourced from the ECB Statistical Data Warehouse. Eurozone ' +
      'Economic Sentiment Indicator is published monthly by the European Commission and interpolated ' +
      'to weekly frequency. HICP data are sourced from Eurostat. The Italy government bond series ' +
      '(RIC .FTIT_TSYUSDT) is denominated in EUR via LSEG currency conversion; the LSEG metadata ' +
      'field "Currency Conversion: EUR" confirms EUR delivery. All series are expressed in or ' +
      'converted to euros prior to return computation.'
    ),
    blankLine(),
    new Paragraph({ children: [run('Appendix E: Reproducibility', { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240, line: 480, lineRule: 'auto' } }),
    bodyPara(
      'All results are generated from a Python codebase (Python 3.11, hmmlearn 0.3.2, scipy 1.13, ' +
      'scikit-learn 1.5, pandas 2.2). The canonical run order is: (1) data pipeline and validation, ' +
      '(2) walk-forward HMM regime estimation, (3) Panel A backtest, (4) Panel B backtest, ' +
      '(5) statistical tests, (6) robustness checks (scripts 10 to 15), (7) FI-expanded universe ' +
      '(scripts 16 to 18). Random seeds are fixed (numpy seed = 42); HMM initialization uses 15 ' +
      'restarts with fixed seed. Raw LSEG source files are subject to data licensing restrictions ' +
      'and cannot be publicly shared; processed parquet files should be treated with equivalent care.'
    ),
    blankLine(),
    ...buildAppendixF(),
  ];
}

// --- APPENDIX F: Descriptive Statistics ---
function buildAppendixF() {
  const hB = { top: TBT, bottom: TB, left: TNB, right: TNB };
  const bB = { top: TB,  bottom: TBT, left: TNB, right: TNB };
  const mB = { top: TNB, bottom: TNB, left: TNB, right: TNB };

  // Descriptive stats table
  const dCols = [2600, 1000, 900, 900, 900, 1060];
  const dHdrs = ['Asset', 'CAGR%', 'Vol%', 'Skewness', 'Ex. Kurt', 'MaxDD%'];
  const dData = [
    ['Bloomberg Commodity',  '2.25',  '15.44', '-0.10', '5.36',  '-63.6'],
    ['Brent Crude Oil',      '12.22', '35.95', '+0.26', '9.51',  '-79.4'],
    ['Gold',                 '12.08', '16.77', '-0.06', '5.33',  '-43.8'],
    ['CAC 40',               '3.47',  '20.64', '-0.73', '8.78',  '-62.8'],
    ['DAX',                  '7.03',  '21.97', '-0.54', '8.31',  '-69.9'],
    ['EuroStoxx 50',         '2.94',  '21.08', '-0.68', '8.56',  '-66.7'],
    ['FTSE MIB',             '2.98',  '22.62', '-0.80', '9.80',  '-74.2'],
    ['IBEX 35',              '4.00',  '21.63', '-0.61', '7.84',  '-61.7'],
    ['STOXX Europe 600',     '3.48',  '17.99', '-0.95', '11.49', '-60.4'],
    ['FTSE EPRA/NAREIT EU',  '3.64',  '19.61', '-1.02', '10.00', '-76.9'],
  ];
  const descTbl = new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: dCols,
    rows: [
      new TableRow({ tableHeader: true, children: dHdrs.map((h, i) => tcell(h, { bold: true, align: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: dCols[i], borders: hB, size: 20 })) }),
      ...dData.map((r, i) => new TableRow({ children: r.map((c, ci) => tcell(c, { align: ci === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT, width: dCols[ci], borders: i === dData.length - 1 ? bB : mB, size: 20 })) })),
    ],
  });

  // Correlation table — 10x10, compact font 17pt to fit
  const labels = ['BComm', 'Brent', 'Gold', 'CAC', 'DAX', 'EuroSx', 'MIB', 'IBEX', 'STOXX', 'EPRA'];
  const corr = [
    [1.00, 0.67, 0.17, 0.25, 0.23, 0.24, 0.22, 0.18, 0.30, 0.26],
    [0.67, 1.00, 0.06, 0.21, 0.17, 0.20, 0.21, 0.18, 0.24, 0.17],
    [0.17, 0.06, 1.00, 0.00, 0.00, -0.01, -0.02, -0.01, 0.00, 0.08],
    [0.25, 0.21, 0.00, 1.00, 0.92, 0.98, 0.89, 0.86, 0.96, 0.65],
    [0.23, 0.17, 0.00, 0.92, 1.00, 0.95, 0.85, 0.82, 0.93, 0.62],
    [0.24, 0.20, -0.01, 0.98, 0.95, 1.00, 0.91, 0.89, 0.96, 0.64],
    [0.22, 0.21, -0.02, 0.89, 0.85, 0.91, 1.00, 0.87, 0.88, 0.63],
    [0.18, 0.18, -0.01, 0.86, 0.82, 0.89, 0.87, 1.00, 0.85, 0.60],
    [0.30, 0.24, 0.00, 0.96, 0.93, 0.96, 0.88, 0.85, 1.00, 0.71],
    [0.26, 0.17, 0.08, 0.65, 0.62, 0.64, 0.63, 0.60, 0.71, 1.00],
  ];
  // Label column wider, data columns even
  const cLabelW = 1060;
  const remaining = CONTENT - cLabelW;
  const cDataW = Math.floor(remaining / 10);
  const cRemainder = remaining - cDataW * 10;
  const cCols = [cLabelW + cRemainder, ...Array(10).fill(cDataW)];
  const corrTbl = new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: cCols,
    rows: [
      // Header row
      new TableRow({
        tableHeader: true,
        children: [
          tcell('', { bold: true, width: cCols[0], borders: hB, size: 17 }),
          ...labels.map((l, i) => tcell(l, { bold: true, align: AlignmentType.RIGHT, width: cCols[i + 1], borders: hB, size: 17 })),
        ],
      }),
      // Data rows
      ...corr.map((row, ri) => new TableRow({
        children: [
          tcell(labels[ri], { bold: false, align: AlignmentType.LEFT, width: cCols[0], borders: ri === corr.length - 1 ? bB : mB, size: 17 }),
          ...row.map((v, ci) => tcell(v.toFixed(2), { align: AlignmentType.RIGHT, width: cCols[ci + 1], borders: ri === corr.length - 1 ? bB : mB, size: 17 })),
        ],
      })),
    ],
  });

  return [
    new Paragraph({ children: [run('Appendix F: Asset Return Descriptive Statistics and Correlations', { italics: true })], alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240, line: 480, lineRule: 'auto' } }),
    bodyPara(
      'Table F.1 reports annualized summary statistics for the ten risky assets in the baseline ' +
      'investable universe. Statistics are computed from weekly simple returns over January 2000 to ' +
      'April 2026 (approximately 1,370 weekly observations). CAGR and volatility are annualized by ' +
      'factors of 52 and sqrt(52), respectively. Excess kurtosis is reported relative to the normal ' +
      'distribution (kurtosis = 0 for normal). MaxDD is peak-to-trough drawdown over the full ' +
      'sample. All six European equity indices exhibit negative skewness and excess kurtosis ' +
      'consistent with fat-tailed return distributions. Brent crude oil has the highest volatility ' +
      '(35.95%) and the most extreme kurtosis (9.51), reflecting periodic supply-shock spikes. ' +
      'Gold and Bloomberg Commodity exhibit near-zero skewness, consistent with their role as ' +
      'diversifying assets in the CVaR LP.'
    ),
    blankLine(),
    ...tblCaption(
      'Table A1',
      'Descriptive Statistics: Risky Asset Returns, January 2000 to April 2026',
      'Weekly simple returns, approximately 1,370 observations. CAGR = compound annual growth rate ' +
      '(weekly compounding, factor 52). Vol = annualized standard deviation (* sqrt(52)). ' +
      'Skewness and excess kurtosis computed from weekly return distribution. MaxDD = peak-to-trough ' +
      'maximum drawdown over full sample. Annualization factor: 52 weeks per year.'
    ),
    descTbl,
    blankLine(),
    // Fixed: "range: −0.02 to +0.08" -> "-0.02 to +0.08"
    bodyPara(
      'Table F.2 reports pairwise return correlations for the same period. The six European equity ' +
      'indices are highly co-integrated, with pairwise correlations ranging from 0.82 (DAX-IBEX) to ' +
      '0.98 (CAC-EuroStoxx 50). Gold has near-zero or slightly negative correlation with all equity ' +
      'indices (range: -0.02 to +0.08), explaining its persistent presence in CVaR-optimal portfolios ' +
      'as a tail-risk diversifier. Brent and Bloomberg Commodity are moderately correlated (0.67), ' +
      'reflecting shared energy exposure. The STOXX Europe 600 has high correlation with the ' +
      'individual European equity indices (0.60 to 0.71), consistent with its role as a cap-' +
      'weighted aggregate of those markets.'
    ),
    blankLine(),
    ...tblCaption(
      'Table A2',
      'Pairwise Return Correlations: Risky Asset Returns, January 2000 to April 2026',
      'Pairwise Pearson correlations of weekly simple returns, approximately 1,370 observations. ' +
      'Asset abbreviations: BCOM = Bloomberg Commodity Index; Brent = Brent Crude Oil (front month); ' +
      'Gold = Gold Spot USD/oz; CAC = CAC 40; DAX = DAX 40; ESTX = EuroStoxx 50; MIB = FTSE MIB; ' +
      'IBEX = IBEX 35; STOXX = STOXX Europe 600; SDAX = SDAX Small Cap.'
    ),
    corrTbl,
    blankLine(),
  ];
}


// ─── DOCUMENT ASSEMBLY ────────────────────────────────────────────────────────

function buildDoc(blinded = false) {
  const { Header, Footer, PageNumber, TabStopType, FieldInstruction } = require('docx');
  // MDPI Economies header: "Economies 2026, 14, x FOR PEER REVIEW   2 of N"
  // Footer: DOI
  const journalHeader = 'Economies 2026, 14, x FOR PEER REVIEW';
  const doiUrl = 'https://doi.org/10.3390/xxxxx';
  return new Document({
    creator: 'build_paper_ECONOMIES.js',
    title: 'Macro-Financial Regime Detection and Portfolio Allocation: Evidence from European Multi-Asset Markets',
    styles: {
      default: {
        document: { run: { font: 'Palatino Linotype', size: 20 } },
      },
    },
    sections: [{
      properties: {
        page: {
          size: { width: PAGE_W, height: PAGE_H },
          margin: { top: TB_MARGIN, right: SIDE_MARGIN, bottom: BOT_MARGIN, left: SIDE_MARGIN },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            children: [
              new TextRun({ text: journalHeader, font: 'Palatino Linotype', size: 18 }),
              new TextRun({ text: '\t', font: 'Palatino Linotype', size: 18 }),
              new TextRun({ children: [PageNumber.CURRENT], font: 'Palatino Linotype', size: 18 }),
              new TextRun({ text: ' of ', font: 'Palatino Linotype', size: 18 }),
              new TextRun({ children: [PageNumber.TOTAL_PAGES], font: 'Palatino Linotype', size: 18 }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: CONTENT }],
            spacing: { before: 0, after: 0, line: 240, lineRule: 'auto' },
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            children: [
              new TextRun({ text: doiUrl, font: 'Palatino Linotype', size: 18 }),
            ],
            alignment: AlignmentType.LEFT,
            spacing: { before: 0, after: 0, line: 240, lineRule: 'auto' },
          })],
        }),
      },
      children: [
        ...buildFrontMatter(blinded),
        ...buildSection1(),
        ...buildSection2(),
        ...buildSection3(),
        ...buildSection4(),
        ...buildSection5(),
        ...buildBackMatter(blinded),
        ...buildReferences(),
        ...buildAppendices(),
        ...buildAppendixF(),
      ],
    }],
  });
}

const PAPER_DIR = require('path').join(__dirname, 'drafts') + '/';

// Build FULL version
Packer.toBuffer(buildDoc(false)).then(buf => {
  const fname = 'paper_draft_ECONOMIES_MDPI_FULL_v7.docx';
  fs.writeFileSync(PAPER_DIR + fname, buf);
  console.log('Written:', fname, `(${(buf.length / 1024).toFixed(0)} KB)`);
}).catch(e => { console.error('FULL build error:', e); process.exit(1); });

// Build BLINDED version
Packer.toBuffer(buildDoc(true)).then(buf => {
  const fname = 'paper_draft_ECONOMIES_MDPI_BLINDED_v7.docx';
  fs.writeFileSync(PAPER_DIR + fname, buf);
  console.log('Written:', fname, `(${(buf.length / 1024).toFixed(0)} KB)`);
}).catch(e => { console.error('BLINDED build error:', e); process.exit(1); });
R_DIR + fname, buf);
  console.log('Written:', fname, `(${(buf.length / 1024).toFixed(0)} KB)`);
}).catch(e => { console.error('BLINDED build error:', e); process.exit(1); });

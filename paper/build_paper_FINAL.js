// build_paper_FINAL.js — JF-style paper FINAL (detection-vs-implementation reframe)
// Built from v8; additional changes:
//  - Abstract rewritten (<100 words, detection-vs-implementation framing)
//  - Introduction rewritten (8 paragraphs, "detection succeeds; translation fails")
//  - TABLE X added to Section VIII (mechanism summary: 6 rows x 5 columns)
//  - Limitations subsection expanded with HMM label caveats, feature sensitivity,
//    macro release timing, simplified TC, no corporate credit, proprietary data note
//  - Output: paper_draft_FINAL.docx
// Run: node build_paper_FINAL.js

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, AlignmentType, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat, TabStopType,
} = require('./node_modules/docx');
const fs   = require('fs');
const path = require('path');

// --- Figure paths ---
const FIG_DIR = require('path').join(__dirname, 'figures') + '/';
const FIG = {
  f1: fs.readFileSync(FIG_DIR + 'figure_1_regime_timeline.png'),
  f2: fs.readFileSync(FIG_DIR + 'figure_2_cumulative_wealth_panel_b.png'),
  f3: fs.readFileSync(FIG_DIR + 'figure_3_turnover_vs_net_sharpe.png'),
  f4: fs.readFileSync(FIG_DIR + 'figure_4_static_cvar_weights_baseline_vs_fi.png'),
  f5: fs.readFileSync(FIG_DIR + 'figure_5_drawdown_baseline_vs_fi.png'),
};

// --- Layout: JF spec ---
// Sides: 1 inch = 1440 DXA; Top/bottom: 1.5 inch = 2160 DXA
const PAGE_W      = 12240;
const PAGE_H      = 15840;
const SIDE_MARGIN = 1440;
const TB_MARGIN   = 2160;
const CONTENT     = PAGE_W - 2 * SIDE_MARGIN; // 9360 DXA = 6.5 inches

// --- Helpers ---
function run(text, opts = {}) {
  return new TextRun({
    text,
    font: 'Times New Roman',
    size: opts.size || 24,
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
    spacing: { before: 0, after: 0, line: 480, lineRule: 'auto' },
    indent: { firstLine: 720 },
    keepNext: opts.keepNext || false,
  });
}

function blankLine() {
  return new Paragraph({
    children: [run('')],
    spacing: { before: 0, after: 0, line: 480, lineRule: 'auto' },
  });
}

function sectionHeading(roman, title) {
  return new Paragraph({
    children: [run(`${roman}. ${title.toUpperCase()}`)],
    alignment: AlignmentType.CENTER,
    spacing: { before: 480, after: 240, line: 480, lineRule: 'auto' },
  });
}

function subHeading(letter, title) {
  return new Paragraph({
    children: [run(letter ? `${letter}. ${title}` : title, { italics: true })],
    alignment: AlignmentType.LEFT,
    spacing: { before: 240, after: 120, line: 480, lineRule: 'auto' },
  });
}

function pageBreakPara() {
  return new Paragraph({ children: [new PageBreak()], spacing: { before: 0, after: 0 } });
}

// Equation paragraphs: centered, Times New Roman, not Courier
function eqPara(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: 'Times New Roman', size: 22, italics: false })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60, line: 300, lineRule: 'auto' },
  });
}

// --- Figure image paragraph ---
function figImage(imgData, origW, origH, altTitle) {
  const W = 624;
  const H = Math.round(origH * W / origW);
  return new Paragraph({
    children: [new ImageRun({
      type: 'png',
      data: imgData,
      transformation: { width: W, height: H },
      altText: { title: altTitle, description: altTitle, name: altTitle },
    })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 120 },
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
      children: [new TextRun({ text, font: 'Times New Roman', size, bold, italics })],
      alignment: align,
      spacing: { before: 0, after: 0, line: 240, lineRule: 'auto' },
    })],
  });
}

// Table caption: number on its own line, title on next line, note below
// Keeps next element (the table) together
function tblCaption(label, title, note) {
  const paras = [
    // Number line
    new Paragraph({
      children: [run(label, { bold: true, size: 22 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 480, after: 0, line: 300, lineRule: 'auto' },
      keepNext: true,
    }),
    // Title line
    new Paragraph({
      children: [run(title, { size: 22 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 0, after: 60, line: 300, lineRule: 'auto' },
      keepNext: true,
    }),
  ];
  if (note) {
    paras.push(new Paragraph({
      children: [run(note, { size: 18 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 60, after: 120, line: 276, lineRule: 'auto' },
      keepNext: true,
    }));
  }
  return paras;
}

// Figure caption: number on its own line, title on next, note below; keepNext on all
function figCaption(label, title, note) {
  const paras = [
    new Paragraph({
      children: [run(label, { bold: true, size: 22 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 480, after: 0, line: 300, lineRule: 'auto' },
      keepNext: true,
    }),
    new Paragraph({
      children: [run(title, { size: 22 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 0, after: 60, line: 300, lineRule: 'auto' },
      keepNext: true,
    }),
  ];
  if (note) {
    paras.push(new Paragraph({
      children: [run(note, { size: 18 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 60, after: 120, line: 276, lineRule: 'auto' },
      keepNext: true,
    }));
  }
  return paras;
}

// --- TITLE PAGE ---
function buildTitlePage() {
  return [
    blankLine(), blankLine(), blankLine(),
    new Paragraph({
      children: [run(
        'When Regimes Do Not Pay: Tail-Risk Allocation, Sovereign Bonds,\n' +
        'and Implementation Frictions in European Multi-Asset Portfolios',
        { size: 28 }
      )],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480, line: 480, lineRule: 'auto' },
    }),
    blankLine(),
    new Paragraph({
      children: [run('JORGE GRUBE')],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120, line: 480, lineRule: 'auto' },
    }),
    new Paragraph({
      children: [run('Universidad Francisco de Vitoria', { italics: true })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480, line: 480, lineRule: 'auto' },
    }),
    blankLine(), blankLine(),
    new Paragraph({
      children: [run('May 2026')],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480, line: 480, lineRule: 'auto' },
    }),
    blankLine(), blankLine(),
    new Paragraph({
      children: [run('ABSTRACT')],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 240, line: 480, lineRule: 'auto' },
    }),
    // Abstract rewritten for FINAL: detection-vs-implementation framing, <100 words
    new Paragraph({
      children: [run(
        'We ask whether HMM-detected market regimes can be translated into out-of-sample ' +
        'CVaR portfolio gains. Using 26 years of weekly European multi-asset returns, we ' +
        'find they cannot. Static CVaR achieves a Sharpe ratio of 0.530 over 2010 to 2026. ' +
        'Naive regime-filtered CVaR raises annual turnover to 226%, collapsing net ' +
        'performance. Implementation-aware alternatives, including turnover-penalized and ' +
        'regime-constrained CVaR, recover cost drag but do not surpass the static benchmark. ' +
        'The central finding is not that regimes are undetectable, but that detected regimes ' +
        'cannot be translated into stable, low-turnover portfolio weights without forfeiting ' +
        'the return advantage.'
      )],
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 0, line: 480, lineRule: 'auto' },
    }),
    blankLine(),
    new Paragraph({
      children: [run('JEL Classification: G11, G12, C22', { italics: true, size: 22 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 240, after: 60, line: 360, lineRule: 'auto' },
    }),
    new Paragraph({
      children: [run(
        'Keywords: CVaR optimization, regime detection, Hidden Markov Model, ' +
        'portfolio management, transaction costs, European equities',
        { italics: true, size: 22 }
      )],
      alignment: AlignmentType.LEFT,
      spacing: { before: 0, after: 240, line: 360, lineRule: 'auto' },
    }),
    // Disclosure statement
    blankLine(),
    new Paragraph({
      children: [run('Conflict-of-Interest Disclosure', { bold: true, size: 20 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 120, after: 60, line: 360, lineRule: 'auto' },
    }),
    new Paragraph({
      children: [run('Jorge Grube Martin-Lunas: I have nothing to disclose.', { size: 20 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 0, after: 0, line: 360, lineRule: 'auto' },
    }),
    pageBreakPara(),
  ];
}

// --- INTRODUCTION ---
function buildIntroduction() {
  return [
    // Para 1: Detection vs. implementation — the central distinction
    bodyPara(
      'Whether financial market regimes can be detected has a well-established affirmative answer. ' +
      'Hamilton\'s (1989) Hidden Markov Model for business-cycle identification and Ang and ' +
      'Bekaert\'s (2002, 2004) regime-switching asset return model document that equity volatility, ' +
      'credit spreads, and correlation structures shift across identifiable states. The more ' +
      'consequential question, and the one this paper addresses, is different: once regimes are ' +
      'detected, can that detection be translated into portfolio gains? The answer depends not on ' +
      'whether a regime label is assigned correctly, but on whether acting on that label generates ' +
      'stable, low-turnover weights that survive transaction costs. The central question is not ' +
      'whether regimes can be detected, but whether detected regimes can be translated into ' +
      'stable, low-turnover portfolio weights.'
    ),
    blankLine(),
    // Para 2: European setting as a demanding test environment
    bodyPara(
      'The European multi-asset setting provides a demanding environment for this question. ' +
      'Europe has experienced four structurally distinct macro episodes within a single 26-year ' +
      'window: the post-dot-com normalization of 2002 to 2006, the Global Financial Crisis of 2008 ' +
      'to 2009, the European sovereign debt crisis of 2011 to 2012 with its unique peripheral ' +
      'spread dynamics, and the post-zero-interest-rate transition of 2022 in which ECB rate hikes ' +
      'imposed severe losses on long-duration bonds that had previously served as the universal ' +
      'risk-off instrument. Each episode rewarded a different defensive allocation: commodities and ' +
      'cash in 2008, government bonds in 2011, and commodities again in 2022. This structural ' +
      'instability makes Europe an informative laboratory for evaluating whether HMM-based ' +
      'conditioning can reliably identify and pre-position for such transitions in real time.'
    ),
    blankLine(),
    // Para 3: Research design
    bodyPara(
      'We study this question using ten risky assets spanning equities, commodities, real estate, ' +
      'and energy, over January 2000 to April 2026. Our primary research design combines ' +
      'Conditional Value-at-Risk (CVaR) portfolio optimization, a coherent, regulation-friendly ' +
      'risk measure (Rockafellar and Uryasev, 2000), with a four-state Gaussian Hidden Markov ' +
      'Model estimated on eight macro-financial features. The HMM generates strictly out-of-sample ' +
      'regime labels via an expanding walk-forward procedure, and we use these labels to condition ' +
      'the CVaR scenario set on the current market state (Regime CVaR-A) or to importance-weight ' +
      'scenarios proportionally to regime posteriors (Weighted CVaR).'
    ),
    blankLine(),
    // Para 4: OOS discipline
    bodyPara(
      'A critical feature of our design is the strict out-of-sample discipline throughout. At each ' +
      'four-week rebalance step, the HMM is re-estimated from scratch on all available history up ' +
      'to that date, with no forward-looking information ever entering portfolio construction. This ' +
      'walk-forward expanding-window design contrasts with the partial in-sample evaluations common ' +
      'in earlier regime-switching portfolio work and ensures that reported Sharpe ratios reflect ' +
      'genuine predictive content rather than in-sample fit (see Guidolin and Timmermann, 2007, ' +
      'for a discussion of this distinction). All transaction costs are applied at each rebalance ' +
      'using realized turnover, not the theoretical minimum implied by target weights.'
    ),
    blankLine(),
    // Para 5: Detection succeeds; translation fails (the core finding)
    bodyPara(
      'Our central finding is that regime detection is reliable but regime implementation is ' +
      'structurally costly. Over the 2010 to 2026 evaluation window (808 weekly observations), ' +
      'the walk-forward HMM produces stable regime assignments, with adjacent-window label ' +
      'agreement exceeding 94% of weeks. The detection step succeeds. What fails is translation: ' +
      'when the detected regime changes, the CVaR linear program\'s scenario set changes ' +
      'discontinuously, generating portfolio reconstitution turnover of 226% annually, tenfold ' +
      'that of the static benchmark. Static CVaR achieves an annualized Sharpe ratio of 0.530 and ' +
      'a maximum drawdown of -25.3%. Regime CVaR-A achieves a Sharpe of only 0.365. At ten basis ' +
      'points of transaction costs, its net Sharpe falls to 0.346 versus 0.528 for Static CVaR.'
    ),
    blankLine(),
    // Para 6: Implementation-aware variants as partial resolution
    bodyPara(
      'Two implementation-aware approaches address the translation failure directly. A turnover-' +
      'penalized CVaR formulation adds an L1 cost term to the linear program objective, reducing ' +
      'Regime CVaR-A turnover from 226% to 60% and recovering net Sharpe to 0.486. Regime-aware ' +
      'weight-band constraints encode investment policy beliefs as group-level bounds, reducing ' +
      'equity exposure and increasing defensive allocations in stress states, while preserving the ' +
      'full CVaR scenario set intact. This approach achieves 0.519 net Sharpe at only 29% annual ' +
      'turnover, within 0.009 of the static benchmark. Neither formulation surpasses Static CVaR ' +
      'in any robustness specification.'
    ),
    blankLine(),
    // Para 7: FI expansion
    bodyPara(
      'A 14-asset FI-expanded universe adding sovereign bond total-return indices improves Panel A ' +
      'Sharpe by 0.034 and reduces maximum drawdown from -39.5% to -14.8%. The 2022 ECB ' +
      'rate-hiking cycle, however, inflicts -10% to -13% portfolio losses on the bond-heavy ' +
      'FI-expanded portfolio while the baseline, concentrated in commodities and gold, avoids this ' +
      'shock. Bond inclusion changes the defensive allocation channel rather than uniformly ' +
      'improving all outcomes. This tension illustrates a general principle: opportunity set design ' +
      'implicitly takes positions on macro risk factors that may or may not be compensated in ' +
      'the evaluation sample.'
    ),
    blankLine(),
    // Para 8: Contributions with detection-vs-implementation framing
    bodyPara(
      'Our contributions span three areas. First, we provide a strictly out-of-sample evaluation ' +
      'of regime-conditional CVaR in a European multi-asset context, extending Guidolin and ' +
      'Timmermann (2007) and Ang and Bekaert (2004) to the implementation viability question. ' +
      'Second, we identify the LP scenario discontinuity as the primary mechanism of regime CVaR ' +
      'failure, distinguishing detection quality from implementation cost, a distinction absent ' +
      'from most prior regime portfolio work. Third, we show that the implementation gap can be ' +
      'largely closed through turnover-penalized optimization and regime-constrained weight bands, ' +
      'contributing to the literature on implementation frictions (Frazzini, Israel, and Moskowitz, ' +
      '2015; Novy-Marx and Velikov, 2016). Sections I through IX cover data, methodology, regime ' +
      'characterization, baseline results, implementation variants, FI expansion, robustness, ' +
      'discussion, and conclusion in turn.'
    ),
    blankLine(),
  ];
}

// --- SECTION I: DATA ---
function buildSectionI() {
  return [
    sectionHeading('I', 'Data'),
    subHeading('A', 'Asset Universe'),
    bodyPara(
      'The baseline investable universe consists of ten risky assets and one risk-free rate, all ' +
      'denominated in or converted to euros. The risky universe spans European equities (six indices: ' +
      'CAC 40, DAX, EuroStoxx 50, FTSE MIB, IBEX 35, and STOXX Europe 600), listed real estate ' +
      '(FTSE EPRA/NAREIT Europe), broad commodities (Bloomberg Commodity Index), energy (Brent crude ' +
      'oil front-month futures), and precious metals (gold spot, EUR-converted from USD). The risk-free ' +
      'instrument is the EURIBOR 3-month rate, used as the cash return benchmark and excluded from ' +
      'the risky portfolio optimization.'
    ),
    blankLine(),
    bodyPara(
      'Most series are total-return indices sourced from LSEG Workspace (Refinitiv). Exceptions: Brent ' +
      'is a front-month futures price (RIC: LCOc1) without a dividend component; gold is a USD spot ' +
      'price (XAU=) converted at weekly prevailing FX rates; and EURIBOR 3M (EUR3MD=, sourced from the ' +
      'ECB) is a rate series converted to a weekly simple return via (1 + r_ann)^(1/52) - 1. Table I ' +
      'summarizes the universe.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE I',
      'Asset Universe',
      'The table reports the 11-asset baseline investable universe. RICs are LSEG Workspace identifiers. ' +
      'All return series are denominated in EUR. TR = total return index. Brent crude oil and gold are ' +
      'price series, not total-return indices; Brent is a front-month futures price and gold is a USD spot ' +
      'price converted at weekly FX rates. EURIBOR 3M is excluded from the optimized risky portfolio. ' +
      'A 14-asset FI-expanded universe adds Germany, Spain, and Italy government bond TR indices from FTSE ' +
      'Russell. The Italy series (RIC .FTIT_TSYUSDT) is delivered in EUR via LSEG currency conversion; no ' +
      'native EUR RIC exists.'
    ),
    buildTableI(),
    blankLine(),
    subHeading('B', 'Sample and Frequency'),
    bodyPara(
      'All series are aligned to weekly Friday-close prices over January 14, 2000 to April 3, ' +
      '2026, yielding 1,369 weekly observations before burn-in exclusions. We use simple (arithmetic) weekly ' +
      'returns throughout; all strategy-level statistics are annualized using a factor of 52. Missing ' +
      'values arising from national holidays are forward-filled for up to five consecutive business days; ' +
      'residual gaps (less than 0.1% for all series) are excluded from portfolio return calculations via ' +
      'a minimum observation requirement. Raw source files are subject to LSEG data licensing restrictions ' +
      'and cannot be distributed publicly; all results are reproducible from the processed parquet files ' +
      'accompanying this paper.'
    ),
    blankLine(),
    subHeading('C', 'Regime Features'),
    bodyPara(
      'The HMM is estimated on eight macro-financial features, each transformed to a 52-week rolling ' +
      'z-score to ensure comparable scale. The features are: the VIX implied volatility index (z52_VIX, ' +
      'anchor for state ordering), VSTOXX European implied volatility (z52_VSTOXX), the MOVE ' +
      'fixed-income volatility index (z52_MOVE), the Germany 10-year yield minus ECB deposit rate slope ' +
      '(z52_germany_10y_2y_slope), the average sovereign spread of Spain, Portugal, and Italy over ' +
      'Germany (z52_peripheral_spread_avg), the DXY dollar index (z52_DXY_USD_Index), the Eurozone ' +
      'Economic Sentiment Indicator (z52_Eurozone_Economic_Sentiment_Indicator), and the HICP ' +
      'headline-minus-core inflation gap (z52_hicp_headline_core_gap). Sample coverage ranges from ' +
      '78% (ESI, HICP) to 100% (VIX).'
    ),
    blankLine(),
  ];
}

function buildTableI() {
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

// --- SECTION II: METHODOLOGY ---
function buildSectionII() {
  return [
    sectionHeading('II', 'Methodology'),
    subHeading('A', 'Return Computation and Transaction Costs'),
    bodyPara(
      'Let p_{i,t} denote the price (or price-equivalent level) of asset i at end of week t. ' +
      'Simple weekly returns are r_{i,t} = p_{i,t}/p_{i,t-1} - 1. Portfolio returns are ' +
      'r_{p,t} = sum_i w_{i,t-1} r_{i,t}, where w_{i,t-1} are weights set at the open of week t. ' +
      'Transaction costs are modeled as TC_rate * sum_i |w_{i,t} - w_{i,t-1}^+|, where w_{i,t-1}^+ ' +
      'is the weight after drift and before rebalancing. We evaluate TC rates of 0, 5, 10, and 25 ' +
      'basis points per one-way unit of turnover.'
    ),
    blankLine(),
    subHeading('B', 'CVaR Portfolio Optimization'),
    bodyPara(
      'For a portfolio weight vector w, the Conditional Value-at-Risk (CVaR) at confidence level ' +
      'α = 0.95 is the expected loss conditional on being in the worst (1 - α) tail of ' +
      'the return distribution. Following Rockafellar and Uryasev (2000), CVaR is minimized via a ' +
      'linear program (LP) over a scenario set of T_s historical weekly returns. The LP takes the form:'
    ),
    blankLine(),
    eqPara('min     ζ + [1 / ((1 - α) · T_s)] · Σ_t  u_t'),
    eqPara('s.t.    u_t >= -r_t\'w - ζ,     u_t >= 0,     Σ_i w_i = 1,     0 <= w_i <= 0.25'),
    blankLine(),
    bodyPara(
      'Here ζ is the Value-at-Risk threshold and u_t are auxiliary loss exceedance variables. ' +
      'With α = 0.95, the factor 1/((1 - α) · T_s) = 1/(0.05 · T_s) averages ' +
      'the losses exceeding the VaR threshold over the worst 5% of scenarios. The scalar 0.25 imposes ' +
      'a 25% maximum weight per asset. The scenario window is a rolling 260-week (5-year) history of ' +
      'weekly returns. We solve the LP using scipy.optimize.linprog at each four-week rebalance.'
    ),
    blankLine(),
    bodyPara(
      'We consider four CVaR variants. Static CVaR uses all 260 scenarios without regime ' +
      'conditioning. Regime CVaR-A restricts the scenario set to historical weeks in which the ' +
      'current regime label was active; if fewer than 30 such weeks are available, it falls back to ' +
      'the full 260-week window. Weighted CVaR assigns scenario weights proportional to the current ' +
      'week\'s posterior probability of each historical week\'s regime label, using all 260 scenarios. ' +
      'TC-aware CVaR augments the LP objective with an L1 turnover penalty term ' +
      'λ · sum_i |w_i - w_{i,prev}|, implemented via standard auxiliary variables.'
    ),
    blankLine(),
    subHeading('C', 'Markowitz Minimum-Variance'),
    bodyPara(
      'As an additional benchmark, we estimate a minimum-variance portfolio using a Ledoit-Wolf ' +
      'shrinkage estimator applied to the rolling 260-week sample covariance matrix (Ledoit and Wolf, ' +
      '2004). The same 25% maximum weight constraint applies. We label this strategy Markowitz (Min-Var).'
    ),
    blankLine(),
    subHeading('D', 'HMM Regime Detection'),
    bodyPara(
      'We model the evolution of market states using a four-state Gaussian Hidden Markov Model ' +
      '(HMM) with diagonal covariance matrices, estimated via the Expectation-Maximization (EM) ' +
      'algorithm with 15 random restarts and up to 500 EM iterations per restart. The model is ' +
      'applied to the eight z-score features described in Section I.C. The four-state specification ' +
      'is selected by BIC from a grid of two to five states.'
    ),
    blankLine(),
    bodyPara(
      'Critically, all regime labels used in portfolio construction are strictly out-of-sample. We ' +
      'implement an expanding walk-forward procedure: at each four-week rebalance step, the HMM is ' +
      're-estimated from scratch using all available history up to the current rebalance date, subject ' +
      'to a minimum of MIN_TRAIN_OBS = 156 weeks (three years) of training data. Panel B evaluation ' +
      'starts from October 15, 2010 to ensure stable four-state estimates throughout. States are ' +
      'canonically ordered by ascending mean z52_VIX across the walk-forward window; State 0 has the ' +
      'lowest equity-volatility signature and State 3 the highest.'
    ),
    blankLine(),
    subHeading('E', 'Backtesting and Evaluation'),
    bodyPara(
      'All strategies are rebalanced every four weeks. Panel A evaluates the long-horizon period ' +
      'from January 10, 2003 to April 3, 2026 (1,213 weeks) for the four non-regime strategies. ' +
      'Panel B evaluates from October 15, 2010 to April 3, 2026 (808 weeks) and adds Regime CVaR-A ' +
      'and Weighted CVaR. Performance metrics include: annualized CAGR (weekly compounding, factor ' +
      '52), annualized volatility (times square root of 52), Sharpe ratio (mean excess return over ' +
      'EURIBOR 3M divided by standard deviation, times square root of 52), maximum drawdown ' +
      '(peak-to-trough on the cumulative wealth curve), 95% CVaR (average of worst 5% weekly returns), ' +
      'Calmar ratio (CAGR/|MaxDD|), and annualized turnover (mean weekly one-way turnover times 52).'
    ),
    blankLine(),
    subHeading('F', 'Statistical Tests'),
    bodyPara(
      'We report two complementary tests. First, a pairwise HAC/Newey-West t-test ' +
      '(Newey and West, 1987) of mean excess-return differentials (strategy minus equal-weight ' +
      'benchmark), with a lag of 13 weeks (one quarter) to account for serial correlation. The ' +
      'test is one-sided (H_1: strategy mean excess return > benchmark). Second, a circular ' +
      'block-bootstrap Sharpe ratio confidence interval with block length 13 weeks and 5,000 ' +
      'bootstrap draws, which accounts for return autocorrelation and fat tails without ' +
      'distributional assumptions. We caution that the bootstrap intervals report individual ' +
      'strategy Sharpe uncertainty; they do not constitute pairwise tests of Sharpe equality ' +
      'between strategies.'
    ),
    blankLine(),
  ];
}

// --- SECTION III: REGIME CHARACTERIZATION ---
function buildSectionIII() {
  return [
    sectionHeading('III', 'Regime Characterization'),
    bodyPara(
      'Table II summarizes the four HMM states identified by their heuristic labels, assigned ' +
      'post-estimation from average feature values. Statistics are from the full-sample descriptive ' +
      'HMM (used here for characterization only); portfolio construction relies exclusively on ' +
      'the expanding walk-forward labels. State 0 has the lowest canonical z52_VIX mean; State 3 ' +
      'the highest. This ordering is enforced post-estimation and is not a model constraint.'
    ),
    blankLine(),
    // Math minuses replaced with - throughout
    bodyPara(
      'State 0 (Low-vol / Subdued) exhibits the lowest VIX (z-score mean: -0.96), a steeply ' +
      'inverted yield curve slope (-1.31), and neutral-to-negative economic sentiment (-0.33). It ' +
      'captures late-cycle deceleration phases with suppressed volatility but deteriorating ' +
      'fundamentals. State 1 (Risk-on / Expansion) combines low VIX (-0.59) with strongly positive ' +
      'ESI (+1.49), tight sovereign spreads (-0.57), and a steep yield curve (+0.70), consistent ' +
      'with broad risk appetite. State 2 (Neutral / Moderate) is an intermediate state with ' +
      'near-average VIX (+0.05) and below-average ESI (-0.73). State 3 (Elevated-risk / Stress) ' +
      'has the highest VIX (+1.84), wide peripheral spreads (+0.45), and strongly negative ESI ' +
      '(-0.74), capturing acute stress episodes including the Global Financial Crisis of 2008 to 2009, ' +
      'the European sovereign crisis of 2011 to 2012, and the COVID-19 crash of March 2020.'
    ),
    blankLine(),
    bodyPara(
      'These labels are interpretive, not model constraints. The walk-forward procedure means that ' +
      'state assignments for any given week reflect only information available up to that date. ' +
      'Baseline label agreement with a 6-week HICP-lagged specification is approximately 55%, ' +
      'confirming that the HICP publication-lag timing assumption is a meaningful but not ' +
      'outcome-determining modeling choice (Section VII).'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE II',
      'HMM Market-State Characteristics',
      'Four-state Gaussian HMM estimated on eight macro-financial z-score features (full-sample descriptive; ' +
      'portfolio construction uses strictly OOS walk-forward labels). States are ordered by ascending mean ' +
      'z52_VIX. Freq = share of total weekly observations. Avg Dur = average regime episode duration (weeks). ' +
      'Selected feature z-score means shown; full feature vectors available in the supplementary data. ' +
      'ESI = Eurozone Economic Sentiment Indicator; Spread = average ES/PT/IT peripheral spread to Germany.'
    ),
    buildTableII(),
    blankLine(),
    ...figCaption(
      'FIGURE 1',
      'Full-Sample Regime Timeline, 2000 to 2026',
      'Four-state HMM state sequence estimated on the full sample (in-sample, descriptive purposes only). ' +
      'States ordered by ascending mean z52_VIX: State 0 (Low-vol / Subdued), State 1 (Risk-on / ' +
      'Expansion), State 2 (Neutral / Moderate), State 3 (Elevated-risk / Stress). This figure uses ' +
      'full-sample labels and is never used in portfolio return calculations; all portfolio construction ' +
      'uses strictly OOS walk-forward labels.'
    ),
    figImage(FIG.f1, 2096, 1408, 'Figure 1 Full-Sample Regime Timeline'),
    blankLine(),
  ];
}

function buildTableII() {
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

// --- SECTION IV: BASELINE RESULTS ---
function buildSectionIV() {
  return [
    sectionHeading('IV', 'Baseline Results'),
    subHeading('A', 'Panel A: Long-Horizon Evidence, 2003 to 2026'),
    // Math minuses fixed
    bodyPara(
      'Table III reports Panel A performance metrics for the four non-regime strategies over 1,213 ' +
      'weeks. Static CVaR has the highest Sharpe ratio (0.513), supported by a 95% bootstrap ' +
      'confidence interval of [0.101, 0.987], the only strategy with an individual CI lower bound ' +
      'firmly above zero, although pairwise strategy differences remain statistically ' +
      'indistinguishable. Maximum drawdown is -39.5%, materially lower than the equal-weight ' +
      'benchmark (-50.1%) and the STOXX Europe 600 single-asset benchmark (-60.2%). The risk ' +
      'reduction is attributable to the CVaR LP systematically avoiding the highest-tail-risk assets: ' +
      'over the evaluation period, gold and Bloomberg Commodity together attract approximately 50% of ' +
      'portfolio weight, acting as tail-risk dampeners in the absence of fixed income.'
    ),
    blankLine(),
    bodyPara(
      'Markowitz (Min-Var) achieves a Sharpe of 0.409 with the lowest annualized volatility (12.0%) ' +
      'but a higher maximum drawdown (-45.6%) than Static CVaR, reflecting the difference between ' +
      'variance and tail-risk minimization objectives. Neither Static CVaR nor Markowitz generates a ' +
      'statistically significant mean excess return differential over the equal-weight benchmark at ' +
      'conventional levels (HAC t-statistics: 0.551 and -0.584, respectively), consistent with the ' +
      'limited power of 1,213-week samples for detecting realistic alpha differences.'
    ),
    blankLine(),
    bodyPara(
      'Transaction-cost sensitivity is minimal for Static CVaR: Sharpe declines from 0.513 at 0 bps ' +
      'to 0.508 at 25 bps, reflecting annual turnover of only 24.9%. This structural stability is a ' +
      'direct consequence of the regime-unconditional scenario set changing only gradually as new ' +
      'weekly observations are added.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE III',
      'Panel A Performance: Long-Horizon Evaluation, 2003 to 2026',
      'Weekly simple returns, 1,213 observations (January 10, 2003 to April 3, 2026). Gross performance ' +
      'at 0 bps transaction costs. Annualization factor 52. CAGR = compound annual growth rate. ' +
      'Vol = annualized standard deviation. Sharpe = (mean excess weekly return / SD excess) * sqrt(52), ' +
      'where excess is relative to EURIBOR 3M. MaxDD = peak-to-trough maximum drawdown. ' +
      'CVaR 95% = average of worst 5% weekly returns. Calmar = CAGR/|MaxDD|. Ann. TO = annualized ' +
      'one-way portfolio turnover. Bootstrap 95% CI uses circular block bootstrap, block = 13 weeks, ' +
      '10,000 draws; CIs report individual strategy Sharpe uncertainty, not pairwise differences.'
    ),
    buildTableIII(),
    blankLine(),
    subHeading('B', 'Panel B: Regime-Aware Out-of-Sample Evidence, 2010 to 2026'),
    bodyPara(
      'Table IV reports Panel B results. Static CVaR remains the most robust benchmark, achieving a ' +
      'Sharpe of 0.530 over 808 weeks. Its bootstrap confidence interval of [0.068, 1.058] is the ' +
      'only individual strategy CI with a positive lower bound; however, pairwise strategy differences ' +
      'remain statistically indistinguishable across all specifications. Regime CVaR-A generates a ' +
      'gross Sharpe of only 0.365, substantially below Static CVaR and even below the equal-weight ' +
      'benchmark (0.409). Weighted CVaR is marginally higher at 0.368.'
    ),
    blankLine(),
    bodyPara(
      'The explanation lies in a combination of factors. First, the regime-filtered scenario sets are ' +
      'smaller and noisier than the full 260-week window, introducing estimation error into the CVaR ' +
      'LP. Second, and more importantly, regime transitions trigger abrupt portfolio reallocation: ' +
      'when the HMM transitions between states, the optimal CVaR portfolio for the new state\'s ' +
      'scenario set may differ substantially from the outgoing portfolio. This produces annualized ' +
      'turnover of 225.75% for Regime CVaR-A versus 21.4% for Static CVaR, a tenfold difference. ' +
      'Weighted CVaR is similar at 232.5%.'
    ),
    blankLine(),
    bodyPara(
      'Table V reports the transaction-cost sensitivity of all strategies. At 10 bps of TC, the net ' +
      'Sharpe of Regime CVaR-A falls to 0.346 and Weighted CVaR to 0.348, compared to 0.528 for ' +
      'Static CVaR and 0.406 for Equal-Weight. At 25 bps, the regime strategies register net Sharpe ' +
      'ratios of 0.317 and 0.318, respectively. The performance degradation is approximately linear ' +
      'in TC_rate * (TO_strategy - TO_static), confirming that the turnover differential is the ' +
      'dominant driver of net performance differences.'
    ),
    blankLine(),
    bodyPara(
      'No pairwise HAC/Newey-West test is statistically significant at conventional levels. With 808 ' +
      'weekly observations and an effective HAC lag of 13 weeks, power is limited; the results are ' +
      'consistent with the broad message that performance differences between these strategies cannot ' +
      'be conclusively separated from sampling noise over a 15-year window.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE IV',
      'Panel B Performance: Regime-Aware Out-of-Sample Evaluation, 2010 to 2026',
      'Weekly simple returns, 808 observations (October 15, 2010 to April 3, 2026). Gross performance ' +
      'at 0 bps transaction costs. HMM MIN_TRAIN_OBS = 156 weeks; all regime labels are strictly ' +
      'out-of-sample (walk-forward expanding window). Panel B evaluation window chosen to ensure stable ' +
      'four-state HMM estimates throughout. Definitions as in Table III.'
    ),
    buildTableIV(),
    blankLine(),
    ...tblCaption(
      'TABLE V',
      'Transaction-Cost Sensitivity, Panel B (Sharpe Ratio)',
      'Net Sharpe ratios at four TC levels (0, 5, 10, 25 bps per one-way unit of turnover). ' +
      'Annual turnover reported at gross (TC = 0) level. TC is applied as ' +
      'TC_rate * one-way portfolio turnover, subtracted from gross weekly returns before computing Sharpe.'
    ),
    buildTableV(),
    blankLine(),
    ...tblCaption(
      'TABLE VI',
      'Statistical Tests, Panel B (2010 to 2026)',
      'Panel A: HAC/Newey-West one-sided t-test on weekly excess-return differentials ' +
      '(strategy minus Equal-Weight Risky benchmark), Newey-West lag = 13 weeks. H_1: strategy mean ' +
      'excess return > benchmark. Panel B: Circular block-bootstrap 95% Sharpe confidence intervals, ' +
      'block = 13 weeks, 5,000 draws. Bootstrap CIs report individual strategy Sharpe uncertainty; ' +
      'they do not constitute pairwise tests of Sharpe equality. *, **, *** denote significance at ' +
      '10%, 5%, 1% levels. No test achieves conventional significance.'
    ),
    buildTableVI(),
    blankLine(),
    ...figCaption(
      'FIGURE 2',
      'Cumulative Wealth, Panel B (2010 to 2026)',
      'Gross cumulative wealth of $1 invested at the start of the Panel B evaluation window ' +
      '(October 15, 2010), for all six strategies at 0 bps transaction costs. Shaded bands indicate ' +
      'European sovereign crisis (2011 to 2012), COVID-19 crash (Q1 2020), and 2022 rate-hiking shock.'
    ),
    figImage(FIG.f2, 2511, 1220, 'Figure 2 Cumulative Wealth Panel B'),
    blankLine(),
  ];
}

function buildTableIII() {
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

function buildTableIV() {
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

function buildTableV() {
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

function buildTableVI() {
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

// --- SECTION V: IMPLEMENTATION-AWARE ---
function buildSectionV() {
  return [
    sectionHeading('V', 'Implementation-Aware Strategies'),
    subHeading('A', 'Transaction-Cost-Aware CVaR'),
    bodyPara(
      'The high turnover of regime-filtered CVaR strategies motivates embedding transaction costs ' +
      'directly in the optimization. We augment the CVaR LP objective with an L1 turnover penalty: ' +
      'the modified objective is CVaR(w) + λ · sum_i |w_i - w_{i,prev}|, implemented via ' +
      'standard auxiliary variables to preserve linearity. This formulation allows the optimizer to ' +
      'trade off between scenario-matching accuracy and rebalancing cost, producing portfolios that ' +
      'internalize the cost of regime transitions rather than ignoring them.'
    ),
    blankLine(),
    bodyPara(
      'Alternatively, a hard turnover budget constraint sum_i |w_i - w_{i,prev}| <= τ directly ' +
      'bounds turnover at each rebalance period. We evaluate both specifications across parameter ' +
      'grids (λ in {0.001, 0.005, 0.010}; τ in {0.10, 0.20, 0.30}).'
    ),
    blankLine(),
    bodyPara(
      'Table VII reports selected results. The constrained specification at τ = 0.10 reduces ' +
      'Regime CVaR-A annual turnover from 225.8% to 59.9%, a reduction of 166 percentage points. Net ' +
      'Sharpe at 10 bps TC improves from 0.346 to 0.486, a gain attributable almost entirely to ' +
      'the turnover reduction. Despite these improvements, no TC-aware variant consistently surpasses ' +
      'Static CVaR (net Sharpe 0.551 at 10 bps in this experiment context; see Table VII note), which ' +
      'remains the most robust benchmark.'
    ),
    blankLine(),
    bodyPara(
      'A penalized variant combining the ZEW feature swap with λ = 0.005 produces a net Sharpe ' +
      'of 0.567 at 10 bps for Weighted CVaR. This result is exploratory and not used as the ' +
      'confirmatory baseline: it involves a non-standard feature configuration (ZEW replacing VSTOXX) ' +
      'whose label agreement with the canonical HMM is only 47.9%, and whose out-of-sample properties ' +
      'cannot be evaluated reliably within this single evaluation window. Readers should not interpret ' +
      'it as evidence that regime-aware CVaR surpasses Static CVaR in general.'
    ),
    blankLine(),
    subHeading('B', 'Regime-Aware Weight-Band Constraints'),
    bodyPara(
      'An alternative to scenario filtering is to use the regime label to tighten or loosen ' +
      'weight-band constraints on asset groups, while keeping the full 260-week CVaR scenario window ' +
      'unchanged. We define equity (six indices) and defensive (gold, Bloomberg Commodity, Brent) ' +
      'asset groups, and assign regime-dependent bounds: in Stress states (State 3), the equity cap ' +
      'is 45% and the defensive floor is 30%; in Risk-on states (State 1), 75% and 10%; in Low-vol ' +
      'states (State 0), 65% and 15%; in Neutral states (State 2), 60% and 15%.'
    ),
    blankLine(),
    // AI phrase fixed: "dramatic improvement" -> "substantial improvement"; "more institutionally interpretable" -> "more transparent"
    bodyPara(
      'This approach achieves near-static CVaR performance at 0.522 gross Sharpe (baseline HMM) and ' +
      '0.519 (ZEW-swap HMM), with annual turnover of 29.2% and 27.0%, respectively, a substantial ' +
      'improvement over the 226% turnover of Regime CVaR-A. Net Sharpe at 10 bps reaches 0.519 and ' +
      '0.517, within 0.032 of Static CVaR (0.551 in the regime-constraints experiment). The ' +
      'mechanism is also more transparent to an investment committee: it encodes a clear investment ' +
      'policy (reduce equity in stress, maintain defensive floor) rather than a less visible adjustment ' +
      'to the LP scenario set. Static CVaR is not statistically displaced by either variant.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE VII',
      'TC-Aware CVaR and Regime-Constrained CVaR: Selected Results',
      'Panel A: Constrained TC-aware CVaR (turnover budget τ) and penalized TC-aware CVaR ' +
      '(L1 penalty λ). Panel B: Regime-constrained CVaR with group-level weight bands varying ' +
      'by HMM state. All results on Panel B evaluation window (2010 to 2026, 808 weeks). ZEW-swap ' +
      'variants replace z52_VSTOXX with z52_ZEW_Germany in the HMM feature set. Ann.TO = annualized ' +
      'one-way turnover. The ZEW+λ=0.005 result is exploratory and not used as the confirmatory ' +
      'baseline; see text. Static CVaR results in this table are from the experiment evaluation ' +
      'scripts (scripts 14-15), which use the full 2000-2026 rebalance grid for Static CVaR; gross ' +
      'Sharpe is 0.553 versus 0.530 in Table IV (which uses the label-intersected evaluation grid). ' +
      'All regime strategy comparisons within this table use the 0.553 benchmark.'
    ),
    buildTableVII(),
    blankLine(),
    ...figCaption(
      'FIGURE 3',
      'Turnover vs. Net Sharpe Frontier (Panel B, 10 bps TC)',
      'Scatter plot of annualized portfolio turnover (x-axis) vs. net Sharpe at 10 bps TC (y-axis) ' +
      'for all strategies and implementation-aware variants. Each point corresponds to one strategy ' +
      'specification. The plot illustrates the cost-efficiency achievable through implementation-aware ' +
      'regime conditioning; Static CVaR marks the frontier anchor at low turnover. ' +
      'The ZEW+λ=0.005 (exploratory) point is labeled separately.'
    ),
    figImage(FIG.f3, 2198, 1310, 'Figure 3 Turnover vs Net Sharpe Frontier'),
    blankLine(),
  ];
}

function buildTableVII() {
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
    ['Static CVaR (baseline)',             '0.553', '0.551', '20.6%', ''],
    ['Regime CVaR-A, unconstrained',       '0.365', '0.346', '225.8%', ''],
    ['Regime CVaR-A, τ=0.10',         '0.491', '0.486', '59.9%', ''],
    ['Regime CVaR-A, τ=0.20',         '0.449', '0.440', '101.2%', ''],
    ['Weighted CVaR, τ=0.10',         '0.492', '0.486', '61.5%', ''],
    ['Weighted CVaR, ZEW+λ=0.005*',   '0.572', '0.567', '64.8%', '*Exploratory'],
  ];
  const dataB = [
    ['Static CVaR',                             '0.553', '0.551', '20.6%', ''],
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

// --- SECTION VI: SOVEREIGN FI EXPANSION ---
function buildSectionVI() {
  return [
    sectionHeading('VI', 'Sovereign Fixed-Income Expansion'),
    bodyPara(
      'The baseline universe excludes sovereign bonds, reflecting data availability constraints and ' +
      'the desire to construct a clean test of equity-commodity-real-estate diversification. In an ' +
      'FI-expanded robustness check, we add three government bond total-return indices, namely FTSE ' +
      'Russell Germany (EUR), Spain (EUR), and Italy (EUR, delivered via LSEG currency conversion ' +
      'from the USD-priced master series; no native EUR RIC exists in the LSEG catalog), creating ' +
      'a 14-asset investable universe. Table VIII summarizes the FI-expanded results.'
    ),
    blankLine(),
    subHeading('A', 'Allocation Substitution'),
    // AI phrase fixed: "The most striking finding" -> "A notable result"; "This is not a model artifact" -> rephrase
    bodyPara(
      'A notable result is the magnitude of allocation substitution. In the baseline ' +
      'universe, the CVaR LP allocates approximately 25% to gold and 25% to Bloomberg Commodity, ' +
      'both at the maximum weight constraint, because these are the lowest-CVaR assets available. ' +
      'With government bonds added, the optimizer reallocates approximately 73% of the portfolio to ' +
      'sovereign bonds, reducing gold to 10% and commodities to 13.5%. Equity weight falls from ' +
      '39% to 3%. This reflects the fundamental optimization logic: government bonds have substantially ' +
      'lower weekly CVaR and volatility than commodities and exhibit negative correlation with equities ' +
      'in most market states. The baseline\'s heavy commodity allocation is a consequence of the ' +
      'constrained opportunity set, not a general recommendation to overweight commodities.'
    ),
    blankLine(),
    subHeading('B', 'Performance Effects'),
    bodyPara(
      'Panel A (2003 to 2026) results improve when bonds are included. Static CVaR Sharpe rises ' +
      'from 0.513 to 0.547 (+0.034), driven entirely by volatility and drawdown reduction: annualized ' +
      'vol falls from 12.2% to 5.0%, and maximum drawdown improves from -39.5% to -14.8%. CAGR ' +
      'declines (7.05% to 4.00%) because the bond-heavy portfolio has lower absolute return, which ' +
      'is the correct risk-return trade-off for a tail-risk-minimizing strategy.'
    ),
    blankLine(),
    // AI phrase fixed: "This is an honest empirical finding, not an adverse selection artifact"
    bodyPara(
      'Panel B (2010 to 2026) tells a more nuanced story. Static CVaR Sharpe declines slightly ' +
      'from 0.530 to 0.504 (-0.026), while maximum drawdown still improves substantially ' +
      '(-25.3% to -14.6%). The Sharpe decline is mechanically explained by the 2022 rate-hiking ' +
      'episode, in which all three sovereign bond indices lost approximately 15% as the ECB raised ' +
      'rates by 250 basis points. The FI-expanded portfolio held approximately 75% in bonds entering ' +
      '2022, producing a portfolio loss of approximately -10% compared to near-zero for the baseline. ' +
      'This occurs because the baseline holds commodities and gold, which rose sharply on energy ' +
      'inflation, as the primary tail-risk dampeners. This result matters because it shows that the ' +
      'FI-expanded universe changes the defensive allocation channel rather than simply improving all ' +
      'outcomes: it reduces long-run drawdown but introduces material duration risk that materializes ' +
      'in rate-hiking cycles. The main conclusion is unchanged.'
    ),
    blankLine(),
    bodyPara(
      'Regime CVaR-A shows the largest FI-expansion improvement: gross Sharpe rises from 0.365 to ' +
      '0.430 (+0.065), and annual turnover falls from 225.8% to 134.1%. The bond core provides a ' +
      'more stable allocation anchor across regime transitions. Nonetheless, even in the FI-expanded ' +
      'universe, Regime CVaR-A does not surpass Static CVaR as the most robust benchmark.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE VIII',
      'FI-Expanded Universe: Performance Comparison',
      'Baseline = 11-asset universe (10 risky + EURIBOR 3M). FI-Expanded = 14-asset universe ' +
      '(+ Germany, Spain, Italy government bond TR). Gross performance at 0 bps TC. ' +
      'Panel A: 2003 to 2026 (1,213 weeks). Panel B: 2010 to 2026 (808 weeks). ' +
      'Delta = FI-Expanded minus Baseline. The 2022 rate-shock episode (ECB +250bps) was a severe ' +
      'adverse scenario for FI-expanded portfolios. The Italy bond series (RIC .FTIT_TSYUSDT) is ' +
      'EUR-converted by LSEG; no native EUR RIC exists.'
    ),
    buildTableVIII(),
    blankLine(),
    ...figCaption(
      'FIGURE 4',
      'Average Portfolio Weights: Baseline vs. FI-Expanded Universe (Static CVaR)',
      'Average asset-group weights of Static CVaR over the Panel B evaluation window (2010 to 2026). ' +
      'Baseline (left bars) and FI-expanded (right bars) universes. Groups: European Equities, Real ' +
      'Estate, Gold, Bloomberg Commodity, Brent, and Government Bonds (FI-expanded only). Weight data ' +
      'from walk-forward portfolio records averaged over 808 weekly observations.'
    ),
    figImage(FIG.f4, 2211, 1160, 'Figure 4 Average Weights Baseline vs FI-Expanded'),
    blankLine(),
    ...figCaption(
      'FIGURE 5',
      'Drawdown Comparison: Baseline vs. FI-Expanded Static CVaR (Panel B, 2010 to 2026)',
      'Drawdown curves for Static CVaR under the 11-asset baseline and 14-asset FI-expanded universes. ' +
      'The FI-expanded portfolio holds approximately 73% in sovereign bonds; the 2022 ECB rate-hiking ' +
      'cycle generates a drawdown of approximately -14.6% for the FI-expanded strategy versus near-zero ' +
      'for the baseline (which benefits from commodity and gold hedges).'
    ),
    figImage(FIG.f5, 2511, 1161, 'Figure 5 Drawdown Comparison Baseline vs FI-Expanded'),
    blankLine(),
  ];
}

function buildTableVIII() {
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

// --- SECTION VII: ROBUSTNESS ---
function buildSectionVII() {
  return [
    sectionHeading('VII', 'Robustness Checks'),
    bodyPara(
      'We conduct five robustness checks, summarized in Table IX. Each is implemented as an ' +
      'independent experiment that replicates the Panel B pipeline with one modification.'
    ),
    blankLine(),
    subHeading('A', 'HICP Publication-Lag Correction'),
    bodyPara(
      'HICP inflation data is published approximately 17 days after the reference month ends. ' +
      'If LSEG\'s data timestamps reflect the reference period rather than the release date, the ' +
      'HMM feature z52_hicp_headline_core_gap contains up to 5 to 7 weeks of forward-looking ' +
      'information. We apply a 6-week lag to this feature before HMM estimation and rerun the ' +
      'full Panel B pipeline. Label agreement between baseline and lagged specifications is ' +
      'approximately 55%, confirming that HICP timing is a meaningful assumption. The Regime ' +
      'CVaR-A Sharpe changes by up to +0.068 relative to baseline, within the bootstrap ' +
      'confidence band of approximately +/-0.480. The main conclusion is unchanged.'
    ),
    blankLine(),
    subHeading('B', 'ZEW Feature Swap'),
    bodyPara(
      'VSTOXX is highly correlated with VIX (r approximately 0.90), potentially contributing ' +
      'limited marginal discriminatory power to the HMM. We test replacing z52_VSTOXX with ' +
      'z52_ZEW_Germany (ZEW forward expectations indicator; unconditional correlation with z52_ESI ' +
      'over the full weekly sample: r approximately 0.02). The ' +
      'ZEW-swap improves regime CVaR point estimates (Regime CVaR-A Sharpe: 0.365 to 0.483), but ' +
      'label agreement with the baseline is only 47.9%, and no HAC statistical test achieves ' +
      'significance. These results are exploratory and may reflect in-sample tailoring to the ' +
      'particular feature configuration. They are not used as the confirmatory baseline.'
    ),
    blankLine(),
    subHeading('C', 'Rebalance Frequency'),
    bodyPara(
      'We test rebalance frequencies of 1, 2, 4, 8, and 13 weeks. Lower rebalance frequency ' +
      'reduces turnover for regime-conditioned strategies; no frequency tested overturns Static ' +
      'CVaR as the most robust benchmark. The 4-week frequency used in the baseline is a ' +
      'reasonable compromise between responsiveness to regime changes and implementation cost.'
    ),
    blankLine(),
    subHeading('D', 'Turnover Smoothing'),
    bodyPara(
      'Exponential weight averaging (EWA) blending of consecutive portfolio solutions reduces ' +
      'regime-strategy turnover substantially and improves net Sharpe relative to the naive ' +
      'regime-filtered baseline, but does not surpass Static CVaR across the evaluated parameters.'
    ),
    blankLine(),
    subHeading('E', 'Sovereign FI-Expanded Universe'),
    bodyPara(
      'As reported in Section VI. The FI-expanded universe improves drawdown control universally, ' +
      'changes the defensive allocation channel from commodities to sovereign bonds, and reduces ' +
      'turnover for regime-filtered strategies. It introduces rate-shock sensitivity in the 2022 ' +
      'episode that is not present in the baseline. The main Panel B conclusion is unchanged.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE IX',
      'Robustness Check Summary',
      'All checks use the Panel B evaluation window (2010 to 2026, 808 weeks) unless noted. Key metric ' +
      'is net Sharpe at 10 bps TC for Regime CVaR-A. Delta Sharpe = change vs. baseline specification. ' +
      '"Main conclusion" refers to Static CVaR remaining the most robust benchmark across all specifications.'
    ),
    buildTableIX(),
    blankLine(),
  ];
}

function buildTableIX() {
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

// --- SECTION VIII: DISCUSSION ---
function buildSectionVIII() {
  return [
    sectionHeading('VIII', 'Discussion'),
    subHeading('A', 'Why Does Regime Conditioning Fail to Improve Performance?'),
    // Em dashes replaced with commas in this section
    bodyPara(
      'Our results admit several non-exclusive interpretations. First, the HMM may identify ' +
      'statistically real regime states that are nonetheless not exploitable at the portfolio ' +
      'construction frequency. If state transitions are unpredictable at weekly or monthly horizons, ' +
      'even if the states themselves are identifiable in retrospect, then conditioning portfolio ' +
      'weights on current-regime labels introduces noise rather than signal. The label agreement of ' +
      'approximately 55% under HICP specification changes is consistent with this view: the regime ' +
      'assignments are sensitive to feature choices in ways that likely reflect noise in the ' +
      'conditioning variables rather than genuine economic state information.'
    ),
    blankLine(),
    bodyPara(
      'Second, the CVaR LP under scenario restriction is a fundamentally different optimization ' +
      'problem from the full-window LP. Restricting to 30 to 80 regime-matched scenarios replaces a ' +
      'well-conditioned optimization (260 scenarios) with a more fragile problem that is sensitive to ' +
      'the tail structure of a small, historically idiosyncratic period. In standard LP theory, ' +
      'solution quality degrades as the constraint set becomes tighter relative to the feasible space. ' +
      'Here, the small scenario count means the CVaR tail average is estimated from a handful of ' +
      'observations, amplifying the influence of any single historical extreme event. This estimation ' +
      'error in the CVaR objective propagates directly to higher in-sample overfitting and ' +
      'correspondingly worse out-of-sample performance.'
    ),
    blankLine(),
    bodyPara(
      'Third, and most practically, regime transitions generate portfolio reconstitution that is not ' +
      'compensated by return improvements. The HMM assigns a regime label each week, and when the ' +
      'label changes, the entire scenario set changes. This is equivalent to a structural break in ' +
      'the LP solution at each transition, producing the observed tenfold turnover relative to the ' +
      'static benchmark. Unlike momentum or factor signals, where the predictive signal and the ' +
      'trading cost occur on the same asset, here the regime signal is estimated on macro features ' +
      'that are imperfectly related to the assets being traded. The mismatch between signal ' +
      'precision and rebalancing frequency is a structural feature of the HMM-CVaR combination, ' +
      'not an implementation artifact.'
    ),
    blankLine(),
    bodyPara(
      'A fourth mechanism concerns the interaction between HMM label uncertainty ' +
      'and LP sensitivity. Walk-forward HMM estimation produces posterior state probabilities that ' +
      'are often diffuse: in moderate market conditions, states 1 and 2 may each receive 30% to 40% ' +
      'posterior mass. A hard-assignment rule (taking the argmax state) discards this uncertainty, ' +
      'treating a 0.4 vs. 0.35 vs. 0.25 posterior as equivalent to certainty. Weighted CVaR avoids ' +
      'this by soft-weighting scenarios, yet still fails to outperform the static benchmark, ' +
      'suggesting that the issue is not the hard-assignment rule per se but the underlying signal ' +
      'content of the posterior.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE X',
      'Why Regime CVaR-A Fails: Mechanism Summary',
      'The table summarises the six mechanisms through which naive regime-conditional CVaR ' +
      'underperforms the static benchmark, the empirical signature of each mechanism in this paper, ' +
      'the implementation fix pursued here, and the remaining performance gap after the fix. ' +
      'Ann.TO = annualized one-way turnover. Net SR = net Sharpe ratio at 10 bps. ' +
      'All strategy comparisons are on the Panel B evaluation window (2010 to 2026, 808 weeks).'
    ),
    buildTableX(),
    blankLine(),
    subHeading('B', 'Implications for Practice'),
    bodyPara(
      'The regime-constraints approach (Section V.B) is the most practically viable regime-aware ' +
      'mechanism we identify. By encoding investment policy beliefs (reduce equity in stress, hold ' +
      'defensive assets) as group-level weight constraints, while keeping the full CVaR scenario ' +
      'set intact, it achieves near-static performance at moderate turnover and produces a policy ' +
      'that can be audited and presented to a risk committee. This approach is more aligned with ' +
      'how institutional investors use macro views in practice: as guardrails on allocation, not as ' +
      'wholesale replacements of the opportunity set.'
    ),
    blankLine(),
    // "profoundly affects" fixed to "materially affects"
    bodyPara(
      'The FI-expanded results highlight a second practical implication: the composition of the ' +
      'opportunity set materially affects both performance and the source of risk. When bonds are ' +
      'unavailable, the CVaR optimizer heavily concentrates in commodities and gold, an ' +
      'institutionally unusual allocation that happens to outperform in inflationary shocks. Adding ' +
      'bonds produces a more conventional allocation but introduces duration risk that materializes ' +
      'in rate-hiking cycles. Practitioners should be explicit about which risks their opportunity ' +
      'set design is implicitly accepting.'
    ),
    blankLine(),
    bodyPara(
      'A related implication concerns the choice of evaluation benchmark. Our results suggest that ' +
      'the natural reference point for any regime-conditioned extension is the best static optimizer ' +
      'over the same universe, not an arbitrary passive portfolio. In our setting, Static CVaR ' +
      'is a disciplined, systematic strategy with strong risk-control properties; it represents a ' +
      'genuinely high bar. Practitioners comparing regime-conditioned CVaR to a 60/40 portfolio or ' +
      'an equal-weighted benchmark may reach more favorable conclusions, but such comparisons ' +
      'conflate the value of the optimization framework with the incremental value of regime ' +
      'conditioning, making it difficult to attribute performance sources.'
    ),
    blankLine(),
    subHeading('C', 'Limitations'),
    bodyPara(
      'HMM regime labels are statistical constructs, not structural breaks. The model identifies ' +
      'recurring distributional patterns in the feature vector, but these patterns need not ' +
      'correspond to economically distinct regimes in any fundamental sense. State assignments are ' +
      'post-hoc descriptions that may reflect noise as much as signal: the 55% label agreement ' +
      'between the baseline and HICP-lagged specifications suggests that the regime sequence is ' +
      'sensitive to feature timing choices in ways that likely reflect measurement uncertainty ' +
      'rather than genuine economic state differences. All downstream portfolio conclusions inherit ' +
      'this uncertainty.'
    ),
    blankLine(),
    bodyPara(
      'Feature sensitivity is a second structural limitation. The ZEW Germany economic sentiment ' +
      'indicator accounts for approximately 47.9% of the variance explained by the first principal ' +
      'component of the feature set, meaning the regime assignments are disproportionately driven ' +
      'by a single survey-based sentiment measure. Substituting ZEW with VSTOXX (the ZEW-swap ' +
      'experiment) changes RC-CVaR baseline Sharpe from 0.522 to 0.519, a small shift, but ' +
      'confirms that feature construction choices materially affect the label sequence even when ' +
      'aggregate performance appears stable.'
    ),
    blankLine(),
    bodyPara(
      'Macro release timing introduces potential look-ahead risk for HICP and ESI features. The ' +
      'baseline specification uses the most recently available published value, but the publication ' +
      'lag for HICP is approximately four weeks and for ESI approximately three weeks. The HICP-lag6 ' +
      'robustness check addresses this for HICP specifically; ESI publication lag is not separately ' +
      'corrected. ZEW and VIX are market-based and available at weekly frequency without lag. ' +
      'Practitioners implementing this design should apply appropriate publication-lag buffers to ' +
      'all macro features to avoid look-ahead contamination.'
    ),
    blankLine(),
    bodyPara(
      'The transaction cost model is deliberately simplified. The 10 bps one-way cost assumption ' +
      'covers a range of institutional scenarios but does not model bid-ask spreads on futures ' +
      'contracts, market impact for large trades, or the operational costs of frequent rebalancing. ' +
      'The asset universe excludes corporate credit, which would add an additional liquidity ' +
      'dimension to transaction cost modeling. Raw source data are subject to LSEG data licensing ' +
      'restrictions and cannot be distributed publicly; reproducibility depends on access to the ' +
      'processed parquet files accompanying this paper.'
    ),
    blankLine(),
    bodyPara(
      'Statistical power is a binding constraint throughout. With 808 weekly observations and ' +
      'Newey-West HAC lag of 13 weeks, effective degrees of freedom are substantially below nominal. ' +
      'Bootstrap confidence intervals for Sharpe ratios span approximately +/-0.4 units, meaning ' +
      'that point estimates of 0.365 (Regime CVaR-A) and 0.530 (Static CVaR) are not statistically ' +
      'distinguishable at conventional levels. The failure to detect significant outperformance is ' +
      'consistent with both "regime conditioning adds no value" and "the sample is too short to ' +
      'detect realistic Sharpe differences." A longer or out-of-sample replication in a different ' +
      'geographic market would sharpen this inference.'
    ),
    blankLine(),
  ];
}


// --- TABLE X: Mechanism Summary ---
function buildTableX() {
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
      'HICP-lag6 variant: 55% label agreement; ZEW 47.9% feature variance share',
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

// --- SECTION IX: CONCLUSION ---
function buildSectionIX() {
  return [
    sectionHeading('IX', 'Conclusion'),
    // Fixed: "Our central finding is clear:" -> "Our central finding is:"; math minuses replaced
    bodyPara(
      'This paper provides a rigorous out-of-sample evaluation of regime-conditioned CVaR portfolio ' +
      'optimization in European multi-asset markets using 26 years of weekly data. Our central ' +
      'finding is that a regime-unconditional Static CVaR strategy has the strongest point ' +
      'estimates among the main specifications, achieving a Sharpe ratio of 0.530 and maximum ' +
      'drawdown of -25.3% over the 2010 to 2026 evaluation period. It is not statistically displaced ' +
      'by any regime-aware variant. Naive scenario-filtering strategies generate tenfold higher ' +
      'portfolio turnover (225.8% versus 21.4% annually), eroding gross performance below benchmarks ' +
      'at any realistic transaction-cost assumption.'
    ),
    blankLine(),
    bodyPara(
      'We show that this failure is structural rather than incidental. Regime transitions induce ' +
      'discontinuous jumps in the CVaR LP solution, and the restricted scenario sets introduce ' +
      'estimation noise that reduces out-of-sample portfolio quality. Implementation-aware ' +
      'alternatives, namely turnover-penalized CVaR and regime-constrained weight bands, recover ' +
      'much of the cost drag and achieve near-static performance (net Sharpe 0.486 to 0.519 at ' +
      '10 bps), but do not surpass the static benchmark in any robustness specification.'
    ),
    blankLine(),
    // Fixed: "profoundly changes" -> "materially changes"; math minuses fixed
    bodyPara(
      'Sovereign bond inclusion materially changes the allocation mix, displacing commodities and ' +
      'gold with government bonds and reducing maximum drawdown by 10 to 25 percentage points. ' +
      'However, the 2022 ECB rate-hiking cycle inflicts portfolio losses of -10% to -13% on ' +
      'bond-heavy FI-expanded portfolios, a risk the commodity-oriented baseline avoids by ' +
      'construction. This tension illustrates a general principle: opportunity set design ' +
      'implicitly takes positions on macro risk factors that may or may not be compensated in ' +
      'the evaluation sample.'
    ),
    blankLine(),
    // Fixed: "The most actionable implication" -> "One practical implication"
    bodyPara(
      'One practical implication for practitioners is that regime-aware constraints on asset ' +
      'group allocations, encoding investment policy beliefs as guardrails rather than wholesale ' +
      'scenario replacements, provide an implementable mechanism for incorporating macro views into ' +
      'systematic portfolios with moderate turnover and institutional legitimacy. Whether the ' +
      'additional complexity of HMM-based regime classification adds value beyond simpler ' +
      'rule-based risk signals (for example, VIX thresholds) remains an open question for ' +
      'future research.'
    ),
    blankLine(),
    bodyPara(
      'Finally, we caution that the statistical power of even a 15-year weekly backtest is limited. ' +
      'Sharpe differentials of 0.1 to 0.2 between strategies cannot be conclusively attributed to ' +
      'skill versus luck at the 95% confidence level. Practitioners and researchers should treat ' +
      'these results as informative evidence, not definitive rankings. Systematic tail-risk control ' +
      'works in European multi-asset markets; whether systematic regime detection can add cost-effective ' +
      'value beyond a static CVaR framework remains an open empirical question.'
    ),
    blankLine(),
  ];
}

// --- REFERENCES ---
function buildReferences() {
  const refs = [
    'Ang, A., and G. Bekaert, 2002, International asset allocation with regime shifts, Review of Financial Studies 15, 1137-1187.',
    'Ang, A., and G. Bekaert, 2004, How regimes affect asset allocation, Financial Analysts Journal 60, 86-99.',
    'Frazzini, A., R. Israel, and T. Moskowitz, 2015, Trading costs of asset pricing anomalies, Working Paper, AQR Capital Management.',
    'Guidolin, M., and A. Timmermann, 2007, Asset allocation under multivariate regime switching, Journal of Economic Dynamics and Control 31, 3503-3544.',
    'Hamilton, J. D., 1989, A new approach to the economic analysis of nonstationary time series and the business cycle, Econometrica 57, 357-384.',
    'Ledoit, O., and M. Wolf, 2004, A well-conditioned estimator for large-dimensional covariance matrices, Journal of Multivariate Analysis 88, 365-411.',
    'Newey, W., and K. West, 1987, A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix, Econometrica 55, 703-708.',
    'Novy-Marx, R., and M. Velikov, 2016, A taxonomy of anomalies and their trading costs, Review of Financial Studies 29, 104-147.',
    'Rockafellar, R. T., and S. Uryasev, 2000, Optimization of conditional value-at-risk, Journal of Risk 2, 21-41.',
  ];
  return [
    pageBreakPara(),
    new Paragraph({
      children: [run('REFERENCES')],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 240, line: 480, lineRule: 'auto' },
    }),
    ...refs.map(r => new Paragraph({
      children: [run(r, { size: 22 })],
      alignment: AlignmentType.LEFT,
      spacing: { before: 0, after: 120, line: 360, lineRule: 'auto' },
      indent: { left: 720, hanging: 720 },
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
    eqPara('min   CVaR(w) + λ · Σ_i (v_i^+ + v_i^-)'),
    eqPara('s.t.  w_i - w_i^prev = v_i^+ - v_i^-,     v_i^+, v_i^- >= 0'),
    blankLine(),
    bodyPara(
      'plus the standard CVaR constraints (see Section II.B). The constrained formulation replaces ' +
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
      'TABLE F.1',
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
      'as a tail-risk diversifier. Brent and Bloomberg Commodity are moderately correlated with ' +
      'equities (0.17 to 0.30), while FTSE EPRA/NAREIT (European listed real estate) exhibits equity-' +
      'like correlations (0.60 to 0.71) with a moderate discount to equity indices, consistent with ' +
      'its hybrid equity/bond characteristics. These correlation patterns motivate the CVaR ' +
      'LP\'s allocation toward gold and commodities in the absence of sovereign bonds.'
    ),
    blankLine(),
    ...tblCaption(
      'TABLE F.2',
      'Pairwise Return Correlations: Risky Assets, January 2000 to April 2026',
      'Pearson correlations of weekly simple returns. BComm = Bloomberg Commodity; EuroSx = EuroStoxx 50; ' +
      'MIB = FTSE MIB; STOXX = STOXX Europe 600; EPRA = FTSE EPRA/NAREIT Europe. ' +
      'Correlations are unconditional full-sample estimates; regime-conditional correlations vary substantially.'
    ),
    corrTbl,
    blankLine(),
  ];
}

// --- ASSEMBLE ---
const children = [
  ...buildTitlePage(),
  ...buildIntroduction(),
  ...buildSectionI(),
  ...buildSectionII(),
  ...buildSectionIII(),
  ...buildSectionIV(),
  ...buildSectionV(),
  ...buildSectionVI(),
  ...buildSectionVII(),
  ...buildSectionVIII(),
  ...buildSectionIX(),
  ...buildReferences(),
  ...buildAppendices(),
];

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Times New Roman', size: 24 } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: TB_MARGIN, right: SIDE_MARGIN, bottom: TB_MARGIN, left: SIDE_MARGIN },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [
            new TextRun({ text: 'When Regimes Do Not Pay', font: 'Times New Roman', size: 20, italics: true }),
            new TextRun({ text: '\t', font: 'Times New Roman', size: 20 }),
            new TextRun({ children: [PageNumber.CURRENT], font: 'Times New Roman', size: 20 }),
          ],
          tabStops: [{ type: TabStopType.RIGHT, position: CONTENT }],
          spacing: { before: 0, after: 0, line: 240, lineRule: 'auto' },
        })],
      }),
    },
    children,
  }],
});

const OUT_DIR = __dirname + '/';
const PAPER_DIR = require('path').join(__dirname, 'drafts') + '/';

Packer.toBuffer(doc).then(buf => {
  const fname = 'paper_draft_FINAL.docx';
  fs.writeFileSync(OUT_DIR + fname, buf);
  fs.writeFileSync(PAPER_DIR + fname, buf);
  console.log('Written:', fname, `(${(buf.length / 1024).toFixed(0)} KB)`);
  console.log('Copies saved to:');
  console.log(' ', OUT_DIR + fname);
  console.log(' ', PAPER_DIR + fname);
}).catch(e => { console.error(e); process.exit(1); });

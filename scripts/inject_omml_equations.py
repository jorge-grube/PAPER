"""
inject_omml_equations.py - Post-processes DOCX to replace OMML placeholder paragraphs.
"""
import sys, os, shutil, tempfile, zipfile

M_NS = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

def mr(text, style='i'):
    preserve = ' xml:space="preserve"' if (' ' in text or text.startswith(' ') or text.endswith(' ')) else ''
    return f'<m:r><m:rPr><m:sty m:val="{style}"/></m:rPr><m:t{preserve}>{text}</m:t></m:r>'

def msub(base, sub):
    return f'<m:sSub><m:sSubPr><m:ctrlPr/></m:sSubPr><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>'

def msubsup(base, sub, sup):
    return f'<m:sSubSup><m:sSubSupPr><m:ctrlPr/></m:sSubSupPr><m:e>{base}</m:e><m:sub>{sub}</m:sub><m:sup>{sup}</m:sup></m:sSubSup>'

def mnary_sum(sub_c, body_c):
    return (f'<m:nary><m:naryPr><m:chr m:val="&#x2211;"/><m:limLoc m:val="subSup"/>'
            f'<m:subHide m:val="0"/><m:supHide m:val="1"/></m:naryPr>'
            f'<m:sub>{sub_c}</m:sub><m:sup><m:r><m:t></m:t></m:r></m:sup><m:e>{body_c}</m:e></m:nary>')

def mnary_supsub(sub_c, sup_c, body_c):
    return (f'<m:nary><m:naryPr><m:chr m:val="&#x2211;"/><m:limLoc m:val="undOvr"/>'
            f'<m:subHide m:val="0"/><m:supHide m:val="0"/></m:naryPr>'
            f'<m:sub>{sub_c}</m:sub><m:sup>{sup_c}</m:sup><m:e>{body_c}</m:e></m:nary>')

def mfrac(num_c, den_c):
    return f'<m:f><m:fPr><m:ctrlPr/></m:fPr><m:num>{num_c}</m:num><m:den>{den_c}</m:den></m:f>'

def mlimlow(base_c, lim_c):
    return f'<m:limLow><m:limLowPr><m:ctrlPr/></m:limLowPr><m:e>{base_c}</m:e><m:lim>{lim_c}</m:lim></m:limLow>'

# --- Section 2.4 CVaR objective ---
_Ts       = msub(mr('T','i'), mr('s','i'))
_frac_den = mr('(1 &#x2212; ','p') + mr('&#x3B1;','i') + mr(') &#xB7; ','p') + _Ts
_frac     = mfrac(mr('1','p'), _frac_den)
_sum_sub  = mr('t','i') + mr(' = 1','p')
_sum_body = msub(mr('u','i'), mr('t','i'))
_sigma_ts = mnary_supsub(_sum_sub, _Ts, _sum_body)
OMML_CVAR_OBJ = (mlimlow(mr('min','p'), mr('w, &#x3B6;, u','i')) +
    mr('   ','p') + mr('&#x3B6;','i') + mr(' + ','p') + _frac +
    mr(' &#xB7; ','p') + _sigma_ts)

# --- Section 2.4 CVaR constraints ---
_rt_prime = msubsup(mr('r','i'), mr('t','i'), mr('&#x2032;','p'))
_sigma_i  = mnary_sum(mr('i','i'), msub(mr('w','i'), mr('i','i')))
OMML_CVAR_ST = (mr('s.t.   ','p') + msub(mr('u','i'), mr('t','i')) +
    mr(' &#x2265; &#x2212;','p') + _rt_prime + mr('w','i') +
    mr(' &#x2212; ','p') + mr('&#x3B6;','i') + mr(',  ','p') +
    msub(mr('u','i'), mr('t','i')) + mr(' &#x2265; 0,  ','p') +
    _sigma_i + mr(' = 1,  0 &#x2264; ','p') +
    msub(mr('w','i'), mr('i','i')) + mr(' &#x2264; 0.25','p'))

# --- Appendix A Eq1 ---
vi_plus  = msubsup(mr('v'), mr('i'), mr('+','p'))
vi_minus = msubsup(mr('v'), mr('i'), mr('&#x2212;','p'))
sum_body_app = mr('(','p') + vi_plus + mr(' + ','p') + vi_minus + mr(')','p')
OMML_EQ1 = (mr('min','p') + mr('   CVaR(','p') + mr('w') + mr(') + ','p') +
    mr('&#x3BB;') + mr(' &#xB7; ','p') + mnary_sum(mr('i'), sum_body_app))

# --- Appendix A Eq2 ---
wi      = msub(mr('w'), mr('i'))
wi_prev = msubsup(mr('w'), mr('i'), mr('prev','p'))
OMML_EQ2 = (mr('s.t.   ','p') + wi + mr(' &#x2212; ','p') + wi_prev +
    mr(' = ','p') + vi_plus + mr(' &#x2212; ','p') + vi_minus +
    mr(',  ','p') + vi_plus + mr(', ','p') + vi_minus + mr(' &#x2265; 0','p'))

def make_eq_paragraph(omml_inner, body_indent=2608):
    return (f'<w:p {W_NS} {M_NS}>'
        f'<w:pPr>'
        f'<w:spacing w:before="120" w:after="120" w:line="280" w:lineRule="atLeast"/>'
        f'<w:ind w:left="{body_indent}"/><w:jc w:val="left"/>'
        f'<w:rPr><w:rFonts w:ascii="Palatino Linotype" w:hAnsi="Palatino Linotype"/>'
        f'<w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
        f'</w:pPr>'
        f'<m:oMathPara><m:oMathParaPr><m:jc m:val="left"/></m:oMathParaPr>'
        f'<m:oMath>{omml_inner}</m:oMath>'
        f'</m:oMathPara></w:p>')

def find_para_span(xml, marker):
    search_from = 0
    while True:
        tag_start = xml.find('<w:p', search_from)
        if tag_start == -1:
            return None
        char_after = xml[tag_start+4] if tag_start+4 < len(xml) else ''
        if char_after not in (' ', '>'):
            search_from = tag_start + 1
            continue
        depth = 0
        pos = tag_start
        end = -1
        while pos < len(xml):
            if xml[pos:pos+4] == '<w:p' and xml[pos+4:pos+5] in (' ', '>'):
                depth += 1; pos += 4
            elif xml[pos:pos+5] == '</w:p' and xml[pos+5:pos+6] in ('>', ' '):
                depth -= 1
                if depth == 0:
                    end = pos + xml[pos:].index('>') + 1
                    break
                pos += 5
            else:
                pos += 1
        if end == -1:
            break
        if marker in xml[tag_start:end]:
            return (tag_start, end)
        search_from = tag_start + 1
    return None

def inject_omml(input_docx, output_docx):
    replacements = {
        '__OMML_CVAR_OBJ__': make_eq_paragraph(OMML_CVAR_OBJ),
        '__OMML_CVAR_ST__':  make_eq_paragraph(OMML_CVAR_ST),
        '__OMML_EQ1__':      make_eq_paragraph(OMML_EQ1),
        '__OMML_EQ2__':      make_eq_paragraph(OMML_EQ2),
    }
    print(f'[1/4] Unpacking {input_docx} ...')
    unpack_dir = tempfile.mkdtemp(prefix='docx_omml_')
    try:
        with zipfile.ZipFile(input_docx, 'r') as z:
            z.extractall(unpack_dir)
        doc_xml_path = os.path.join(unpack_dir, 'word', 'document.xml')
        with open(doc_xml_path, 'r', encoding='utf-8') as f:
            doc_xml = f.read()
        print('[2/4] Locating placeholder paragraphs ...')
        hits = []
        for marker, new_para in replacements.items():
            span = find_para_span(doc_xml, marker)
            if span is None:
                print(f'      WARNING: "{marker}" not found -- skipping')
            else:
                hits.append((span, new_para, marker))
                print(f'      Found "{marker}" at chars {span[0]}-{span[1]}')
        if not hits:
            print('      No markers found. Nothing to inject.')
            sys.exit(1)
        hits.sort(key=lambda x: x[0][0], reverse=True)
        print(f'[3/4] Injecting {len(hits)} OMML equation(s) ...')
        for (start, end), new_para, marker in hits:
            doc_xml = doc_xml[:start] + new_para + doc_xml[end:]
            print(f'      Injected OMML for "{marker}"')
        with open(doc_xml_path, 'w', encoding='utf-8') as f:
            f.write(doc_xml)
        print(f'[4/4] Repacking -> {output_docx} ...')
        if os.path.exists(output_docx):
            os.remove(output_docx)
        with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root_dir, _, files in os.walk(unpack_dir):
                for file in files:
                    fp = os.path.join(root_dir, file)
                    zout.write(fp, os.path.relpath(fp, unpack_dir))
        print(f'Done. Output saved to: {output_docx}')
    finally:
        shutil.rmtree(unpack_dir, ignore_errors=True)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python inject_omml_equations.py <input.docx> <output.docx>')
        sys.exit(1)
    inject_omml(sys.argv[1], sys.argv[2])

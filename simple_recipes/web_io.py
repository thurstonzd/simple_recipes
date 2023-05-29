def cursor_results_to_html_table(cur):
    headers = ['<th>' + c.name + '</th>' for c in cur.description]
    
    return '<thead>\n\t<trow>\n\t{0}\n\t</trow>\n</thead>'.format(
        '\t'.join(headers))
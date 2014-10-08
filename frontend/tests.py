d = """./bootstrap/choices.tpl.html
./bootstrap/match-multiple.tpl.html
./bootstrap/match.tpl.html
./bootstrap/select-multiple.tpl.html
./bootstrap/select.tpl.html
./select2/choices.tpl.html
./select2/match-multiple.tpl.html
./select2/match.tpl.html
./select2/select-multiple.tpl.html
./select2/select.tpl.html
./selectize/choices.tpl.html
./selectize/match.tpl.html
./selectize/select.tpl.html"""
b = d.splitlines()
prefix1 = ''
prefix = 'libraries/angular-bootstrap/'
b = map(lambda x: (prefix1 + x[2:], prefix + x[2:]), b)
print b
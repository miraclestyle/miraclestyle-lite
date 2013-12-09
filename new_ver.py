# aktuelni dizajn order klase implementira centralizovane funkcije koje rade agregaciju parametara iz
# datastore, primaju neke parametre i vracaju neke druge, pa se kasnije vraceni parametri upisuju u order objekat
# aktuelni dizajn svu logiku cuva u order klasi i time ne dozvoljava bilo kakvo skaliranje bez izmena na order code base...
# ovaj novi dizajn radi tako sto se order objekat provlaci kroz niz klasa (i njihovih osnovnih funkcija) 
# koje ga transformisu ako je to neophodno
# samim tim ovaj dizajn prati context passing strategiju koja dozvoljava vecu fleksibilnost i skaliranje logike
# sto u aktuelnom dizajnu nije moguce.
# za samu implementaciju novog dizajna Tax, Carrier i Shipping Exclusion ndb modeli nisu potrebni, 
# vec neki entiteti koji ce cuvati pickle....
# prilikom implementacije order klase treba se uraditi refactoring postojeceg code base tako da se on rsclani na 
# odvojene namenske klase koje ce postojati u tools.py, napr: Tax, Carrier, Shipping...
# treba imati na umu da ce order klasa obavezno trpiti izmene zbog novog accounting koncepta...
# ovo je primer Tax klase u tools.py gde se nalaze sve ostale klase koje implementiraju aktivnu logiku...
# ova klasa se instacira u nekoj pickle klasi koja je storana kao company child entity na datastore...
# na isti princip se implementira carrier i shipping exclusion logika..
class Tax():
  unique_id = 'neki unique random ID'
  name = 'VAT'
  sequence = 1
  company = ndb.KeyProperty('3', kind=Company, required=True)
  formula = 'prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency'
  location_exclusion = True # applies to all locations except/applies to all locations listed below
  shipping_address = True # decides wheather tax location is order.shipping_address or order.billing_address
  active = True
  locations = []
  product_categories = []
  carriers = []

  def calculate(**kwargs):
    order = kwargs.get('order')
    if (tax.shipping_address):
      location = order.shipping_address
    else:
      location = order.billing_address
    tax_allowed = False
    # location parametar se uvek mora proslediti metodi, kako bi se uradila ispravna validacija.
    if (tax.locations):
      # Tax everywhere except at the following locations
      if not (tax.location_exclusion):
        tax_allowed = True
        for tax_location in tax.locations:
          p = tax_location._properties
          if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
            if (location.country == tax_location.country):
              tax_allowed = False
              break
          elif not (p['postal_code_from'] and p['postal_code_to']):
            if (location.country == tax_location.country and location.region == tax_location.region):
              tax_allowed = False
              break
          else:
            if (location.country == tax_location.country and location.region == tax_location.region and (location.postal_code >= tax_location.postal_code_from and location.postal_code <= tax_location.postal_code_to)):
              tax_allowed = False
              break
      else:
        # Tax only at the following locations
        for tax_location in tax.locations:
          p = tax_location._properties
          if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
            if (location.country == tax_location.country):
              tax_allowed = True
              break
          elif not (p['postal_code_from'] and p['postal_code_to']):
            if (location.country == tax_location.country and location.region == tax_location.region):
              tax_allowed = True
              break
          else:
            if (location.country == tax_location.country and location.region == tax_location.region and (location.postal_code >= tax_location.postal_code_from and location.postal_code <= tax_location.postal_code_to)):
              tax_allowed = True
              break
    else:
      # u slucaju da taxa nema konfigurisane location exclusions-e onda se odnosi na sve lokacije/onda je to globalna taxa
      tax_allowed = True
    # ako je tax_allowed nakon location check-a onda radimo validaciju po carrier-u i product_category-ju
    if (tax_allowed):
      if (tax.carriers) and (tax.carriers.count(order.carrier_reference)):
        order.carrier_tax_reference = tax.unique_id
      elif not (tax.carriers):
        lines = order.lines
        order.lines = []
        for line in lines:
          if (tax.product_categories) and (tax.product_categories.count(line.product_category)):
            if not (line.tax_references.count(tax.unique_id)):
              line.tax_references.append(tax.unique_id)
          elif not (tax.product_categories):
            if not (line.tax_references.count(tax.unique_id)):
              line.tax_references.append(tax.unique_id)
          order.lines.append(line)
    lines = order.lines
    order.lines = []
    for line in lines:
      tax_subtotal = DecTools.form('0', order.currency)
      for tax in line.tax_references:
        ....
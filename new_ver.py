class CartInit:
  
  def run(user_key, catalog_key):
    # ucitaj postojeci entry na kojem ce se raditi write
    catalog = catalog_key.get()
    company = catalog.company.get()
    entry = Entry.query(Entry.journal == ndb.Key('Journal', 'order'), 
                        Entry.company == company, Entry.state.IN(['cart', 'checkout', 'processing']),
                        Entry.party == user_key
                        ).get()
    # ako entry ne postoji onda ne pravimo novi entry na kojem ce se raditi write
    if not (entry):
      entry = Entry()
      entry.journal = ndb.Key('Journal', 'order')
      entry.company = company
      entry.state = 'cart'
      entry.date = datetime.datetime.today()
      entry.party = user_key
    # proveravamo da li je entry u state-u 'cart'
    if (entry.state != 'cart'):
      # ukoliko je entry u drugom state-u od 'cart' satate-a, onda abortirati pravljenje entry-ja
      # taj abortus bi trebala da verovatno da bude neka "error" class-a koju client moze da interpretira useru
      return 'ABORT'
    else:
      return entry
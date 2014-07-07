from google.appengine.ext import ndb

class Testerson(ndb.Model):
  
  name = ndb.StringProperty()
  
  @classmethod
  def _post_delete_hook(cls, key, future):
    print key, future.get_result()
  
  
f = Testerson(name='foo')
f.put()
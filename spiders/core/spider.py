#!/usr/bin/python
#coding=utf-8
import json,re,logging,time,io,os,hashlib
from log import Log
from url_store import UrlStore
from html_store import HtmlStore
from obj_store import ObjStore
class Spider(Log):
  name = None
  models = None
  concurrencyPer1s=1
  def __init__(self, name=None):
    if name is not None:
      self.name = name
    elif not getattr(self, 'name', None):
      raise ValueError("%s must have a name" % type(self).__name__)
    if not hasattr(self, 'start_urls'):
      self.start_urls = []
    if not hasattr(self, 'url_store'):
      print 'init url_store------------------------'
      self.url_store = UrlStore()
    if not hasattr(self, 'html_store'):
      print 'init html_store------------------------'
      self.html_store = HtmlStore()
    if not hasattr(self, "obj_store"):
      print 'init obj_store------------------------'
      self.obj_store = ObjStore()

    Log.__init__(self,self.name)
    self.url_store.saveUrl(self.start_urls)

  def beforeRequest(self, request):
    # request['proxy']=random.choice(spider_resource.proxyips)
    # self.log(request)
    return request

  def _getResponseStr(self, htmSource,url):
    html=None
    try:
      html=htmSource.decode("utf8")
    except: #Exception as e:
      try:
        html=htmSource.decode("gbk")
      except Exception as err:
        self.log('{},{}'.format(err,url),logging.ERROR)
    return html
  def afterResponse(self, response, cookie, url):
    html = self._getResponseStr(response.read(),url)
    data = {
      "html" : html,
      "header" : response.info().headers,
      "cookie" : cookie,
      "url" : url
    }   
    return html
  def popHtml(self):
    return self.html_store.popHtml()
  def saveHtml(self,url,html):
    if(html):
      self.html_store.saveHtml(url,html)

  def removeScripts(self,html):
    html = re.compile('(?=<[\s]*script[^>]*>)[\s\S]*?(?:</script>)').sub('',html)
    html = re.compile('(?=<[\s]*style[^>]*>)[\s\S]*?(?:</style>)').sub('',html)
    html = re.compile('(?=<!--)[\s\S]*?(?:-->)').sub('',html)
    html = re.compile('(?=<[\s]*link )[\s\S]*?(?:>)').sub('',html)
    html = re.compile('(?=<[\s]*meta )[\s\S]*?(?:>)').sub('',html)
    html = re.compile('(?=<[\s]*object[^>]*>)[\s\S]*?(?:</object>)').sub('',html)
    html = re.compile('</object>').sub('',html)
    html = re.compile('(?=<param )[\s\S]*?(?:/>)').sub('',html)
    return html
  def downloadError(self,url,err=None):
    print url,err

  def saveData(self, data):
    # print data
    if(data):
      objs = json.loads(data)
      for obj in objs:
        if(obj.get("Urls")):
          self.saveUrl(obj)
        else:
          d = obj.get("Data")
          if(d and len(d) > 0):
            self.obj_store.saveObj(d[0])

  # def saveObj(self, data):
  #   self.obj_store.saveObj(data)
  #   # print data
  #   raise NotImplementedError('{}.parse callback is not defined'.format(self.__class__.__name__))

  _downloadPageNum=0
  _startCountTs=time.time()
  def checkConcurrency(self):
    tmSpan = time.time()-self._startCountTs
    if(tmSpan>10):
      if(self._downloadPageNum>(self.concurrencyPer1s*tmSpan)):
        return False
      self._startCountTs=time.time()
      self._downloadPageNum=1
    elif self.url_store.getCount()>0:
      self._downloadPageNum=self._downloadPageNum+1
    return True
  def popUrl(self):
    if(self.checkConcurrency()):
      return self.url_store.popUrl()
    else:
      print 'Downloads are too frequent'
    return None
  def urlCount(self):
    return self.url_store.getCount()
  def saveUrl(self, urls):
    self.url_store.saveUrl(urls)


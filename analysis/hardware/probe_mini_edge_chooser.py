"""Root-operated Edge chooser only. Default is offline; never opens a serial port."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.server
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append(site.getusersitepackages())
from tools import mini_browser_windows as config
from tools import verify_mini_browser as browser
from tools.mini_host_journal import atomic_write_json

SCRIPT = r"""(()=>{
 const state={ready:false,phase:'initial',requests:0,open_attempts_blocked:0,
   serial_opened:false,bytes_transmitted:0,info:null,events:[]};
 window.__edgeChooserProbe=state;
 const record=(kind,data={})=>state.events.push({kind,utc:new Date().toISOString(),...data});
 if(!isSecureContext || !navigator.serial || typeof SerialPort==='undefined'){
   state.phase='unsupported';return;
 }
 // Guard is installed before the only request. No application or transport is loaded.
 Object.defineProperty(SerialPort.prototype,'open',{configurable:false,writable:false,value:async function(){
   state.open_attempts_blocked++;record('serial_open_blocked');
   throw new DOMException('Enumeration only: serial opening is forbidden','NotAllowedError');
 }});
 const request=navigator.serial.requestPort.bind(navigator.serial);
 document.getElementById('choose').addEventListener('click',async event=>{
   if(!event.isTrusted || state.requests!==0)return;
   state.requests++;state.phase='chooser_pending';record('request_intent');
   document.getElementById('choose').disabled=true;
   document.getElementById('status').textContent='Selettore aperto. La seriale non verrà aperta.';
   try{
     const port=await request({filters:[{usbVendorId:0x3654,usbProductId:0x5155}]});
     const info=port.getInfo();state.info={vid:info.usbVendorId,pid:info.usbProductId};
     state.phase=state.info.vid===0x3654&&state.info.pid===0x5155?'metadata_returned':'wrong_metadata';
     record('request_returned',{info:state.info});
   }catch(error){state.phase='request_rejected';state.error=String(error);record('request_rejected',{error:String(error)});}
 });
 state.ready=true;state.phase='ready';record('page_ready');
})()"""
HTML = ("<!doctype html><html lang=it><meta charset=utf-8><title>MINI: solo selettore Edge</title>"
        "<style>body{font:20px system-ui;padding:48px}button{font:inherit;padding:16px}</style>"
        "<h1>Verifica del selettore USB</h1><p id=status>Nessuna apertura seriale o trasmissione.</p>"
        "<button id=choose>Cerca MINI USB</button><script>"+SCRIPT+"</script></html>").encode()


def require(value, message):
    if not value: raise ValueError(message)


def now(): return datetime.now(timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()


def edge_path():
    for root in (os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'),
                 os.environ.get('PROGRAMFILES', 'C:/Program Files')):
        path = Path(root)/'Microsoft/Edge/Application/msedge.exe'
        if path.is_file(): return path.resolve()
    raise FileNotFoundError('Existing Microsoft Edge required; nothing will be installed')


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ('/', '/index.html'):
            self.send_error(404);return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; frame-ancestors 'none'")
        self.send_header('Permissions-Policy', 'serial=(self), usb=(), bluetooth=(), midi=(), camera=(), microphone=()')
        self.send_header('Content-Length', str(len(HTML)));self.end_headers();self.wfile.write(HTML)
    def log_message(self, *_): pass


class BoundedCDP(browser.CDP):
    def call(self, method, params=None):
        self.ws.settimeout(1)
        message_id=self.next_id;self.next_id+=1
        self.ws.send(json.dumps({'id':message_id,'method':method,'params':params or {}}))
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            value=json.loads(self.ws.recv())
            if value.get('id')==message_id:
                require('error' not in value, method+': '+str(value.get('error')))
                return value.get('result',{})
            if len(self.events)<256:self.events.append(value)
        raise TimeoutError('bounded CDP call expired: '+method)


def run(output):
    output=Path(output).resolve()
    require(output.is_relative_to(ROOT/'build') and not output.exists(),'new output directory under build required')
    executable=edge_path();output.mkdir(parents=True);profile=output/'isolated-profile';profile.mkdir()
    args=config.browser_arguments(executable,profile)
    report={'schema':1,'kind':'mini-edge-chooser-only','started_utc':now(),'phase':'prepare',
        'browser_arguments':args,'browser_configuration':config.description(args),
        'maximum_browser_lifetime_seconds':60,'serial_open_permitted':False,'protocol_commands_permitted':False,
        'firmware_mutations':False,'application_connection_verified':False,
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in
            (Path(__file__),Path(config.__file__),Path(browser.__file__),
             ROOT/'tools/launch_mini_desktop_readonly.py',ROOT/'tools/mini_host_journal.py')},
        'page_sha256':sha(HTML)}
    save=lambda:atomic_write_json(output/'report.json',report)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    process=cdp=watchdog=None;expired=threading.Event()
    try:
        save()
        with (output/'browser-stderr.txt').open('wb') as stream:
            process=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=stream,
                                     creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        started=time.monotonic();deadline=started+55
        def stop_owned_browser():
            expired.set()
            if process.poll() is None:process.terminate()
        watchdog=threading.Timer(60,stop_owned_browser);watchdog.daemon=True;watchdog.start()
        report['browser_process_id']=process.pid;save()
        endpoint=profile/'DevToolsActivePort'
        while not endpoint.is_file() and time.monotonic()<min(deadline,started+10):
            require(process.poll() is None,'Edge exited before CDP');time.sleep(.1)
        require(endpoint.is_file(),'Edge CDP unavailable')
        address='http://127.0.0.1:'+endpoint.read_text().splitlines()[0]
        get=lambda suffix:json.loads(urlopen(address+suffix,timeout=2).read())
        report['CDP_http']=address;report['browser']=get('/json/version')
        page=next(p for p in get('/json/list') if p['type']=='page')
        report['CDP_page_websocket']=page['webSocketDebuggerUrl'];cdp=BoundedCDP(page['webSocketDebuggerUrl'])
        for domain in ('Page','Runtime'):cdp.call(domain+'.enable')
        report['origin']=f'http://127.0.0.1:{server.server_port}'
        cdp.call('Page.navigate',{'url':report['origin']+'/'})
        state=None
        while time.monotonic()<deadline:
            state=cdp.evaluate('window.__edgeChooserProbe || null')
            if state and state['ready']:break
            time.sleep(.1)
        require(state and state['ready'],'chooser-only page failed to initialize')
        cdp.call('Page.bringToFront')
        report['before_click_screenshot']=cdp.screenshot(output/'before-click.png')
        report['phase']='request_intent';save()
        cdp.click('#choose')  # One trusted click; no automatic selection in the native chooser.
        while time.monotonic()<deadline:
            state=cdp.evaluate('__edgeChooserProbe');report['state']=state;report['phase']=state['phase'];save()
            require(state['open_attempts_blocked']==0,'unexpected forbidden open attempt')
            if state['phase'] in ('metadata_returned','wrong_metadata','request_rejected'):break
            time.sleep(.5)
        if state and state['phase']=='chooser_pending':report['phase']='chooser_pending_at_deadline'
        try:report['screenshot']=cdp.screenshot(output/'chooser.png')
        except Exception as error:report['screenshot_error']=repr(error)
    except Exception as error:report['error']=repr(error)
    finally:
        if cdp:
            try:cdp.call('Browser.close')
            except Exception as error:report['browser_close_error']=repr(error)
            cdp.ws.close();report['CDP_events']=cdp.events
        if process:
            try:process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.terminate();process.wait(timeout=2);report['owned_browser_terminated']=True
        if watchdog:watchdog.cancel()
        server.shutdown();server.server_close();thread.join(timeout=1)
        report.update(finished_utc=now(),watchdog_expired=expired.is_set(),
            browser_process_stopped=process is None or process.poll() is not None,local_server_stopped=not thread.is_alive())
        save()
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--output',type=Path);args=parser.parse_args(argv)
    require(not(args.execute and args.check_only),'choose check-only or execute')
    if not args.execute:
        result={'browser_started':False,'device_io':False,'serial_open_permitted':False,
                'protocol_commands_permitted':False,'maximum_browser_lifetime_seconds':60}
        if args.check_only:result['edge_executable']=str(edge_path())
    else:
        require(args.output is not None,'new output directory required');result=run(args.output)
    print(json.dumps(result,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())

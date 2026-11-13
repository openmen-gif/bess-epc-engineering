"""Run with LibreOffice's Python (Windows) or /usr/bin/python3 + python3-uno.

Uses an isolated pipe/profile; refreshes TOC and fields before DOCX/PDF export.
"""
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

import uno
from com.sun.star.beans import PropertyValue


def props(**values):
    result = []
    for name, value in values.items():
        prop = PropertyValue()
        prop.Name, prop.Value = name, value
        result.append(prop)
    return tuple(result)


def main():
    source, out, soffice, profile = map(Path, sys.argv[1:5])
    font_paths = []
    if sys.platform == 'win32':
        import ctypes
        for font in (Path(__file__).resolve().parents[1]/'vendor/hhic_word/fonts').glob('*.otf'):
            if ctypes.windll.gdi32.AddFontResourceW(str(font)):
                font_paths.append(font)
    pipe = 'bess_' + uuid4().hex
    # No shared desktop instance or TCP listener.
    flags = {'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
    proc = subprocess.Popen([str(soffice), '-env:UserInstallation='+profile.resolve().as_uri(),
                             '--headless','--norestore','--nodefault',
                             '--accept=pipe,name='+pipe+';urp;StarOffice.ServiceManager'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
    doc = desktop = None
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',local)
        deadline = time.monotonic()+30
        while True:
            try:
                ctx = resolver.resolve('uno:pipe,name='+pipe+';urp;StarOffice.ComponentContext')
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError('LibreOffice UNO startup timed out')
                time.sleep(.2)
        desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',ctx)
        doc = desktop.loadComponentFromURL(source.resolve().as_uri(),'_blank',0,
                                           props(Hidden=True,UpdateDocMode=3,MacroExecutionMode=0))
        if doc is None:
            raise RuntimeError('LibreOffice did not load the document')
        indexes = doc.getDocumentIndexes()
        if indexes.getCount() < 1:
            raise RuntimeError('Native table of contents missing')
        doc.refresh()
        for _ in range(2):
            doc.getTextFields().refresh()
            for i in range(indexes.getCount()):
                indexes.getByIndex(i).update()
        doc.storeAsURL(out.resolve().as_uri(),props(FilterName='Office Open XML Text',Overwrite=True))
        doc.storeToURL(out.with_suffix('.pdf').resolve().as_uri(),props(FilterName='writer_pdf_Export',Overwrite=True))
        print(json.dumps({'indexes_updated':indexes.getCount(),'pdf':str(out.with_suffix('.pdf'))}))
    finally:
        if doc is not None:
            doc.close(True)
        if desktop is not None:
            desktop.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=5)
        if sys.platform == 'win32':
            for font in font_paths:
                ctypes.windll.gdi32.RemoveFontResourceW(str(font))


if __name__ == '__main__':
    main()

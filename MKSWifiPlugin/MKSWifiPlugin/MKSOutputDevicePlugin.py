# Copyright (c) 2021
# MKS Plugin is released under the terms of the AGPLv3 or higher.
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import MKSOutputDevice

from UM.Signal import Signal, signalemitter
from UM.Application import Application
from UM.Logger import Logger

from PyQt6.QtCore import QObject

from UM.Message import Message
from UM.i18n import i18nCatalog

from . import Constants, MKSPreview

catalog = i18nCatalog("mksplugin")


def _serhat_install_gcodewriter_patch():
    """Serhat patch: Monkey-patch the actual GCodeWriter INSTANCE Cura uses
    for text/x-gcode. We resolve it via MeshFileHandler at runtime and patch
    both the instance AND its class in sys.modules, so however Cura invokes
    the writer, our wrapper runs."""
    try:
        from UM.Application import Application as _App
        handler = _App.getInstance().getMeshFileHandler()
        # Find the gcode writer instance regardless of exact mime string
        writer = None
        try_ids = ["text/x-gcode", "application/x-gcode", "text/gcode"]
        for tid in try_ids:
            try:
                w = handler.getWriter(tid)
                if w is not None:
                    writer = w
                    break
            except Exception:
                pass
        if writer is None:
            # Fallback: scan registered writers
            try:
                for mime, w in handler._writers.items():
                    if "gcode" in str(mime).lower():
                        writer = w
                        break
            except Exception:
                pass
        if writer is None:
            Logger.log("w", "MKS SERHAT: could not locate GCodeWriter instance to patch")
            return

        cls = writer.__class__
        Logger.log("d", "MKS SERHAT: found writer instance %r of class %r (module %s)" %
                   (writer, cls.__name__, cls.__module__))

        if getattr(cls, "_serhat_patched", False):
            Logger.log("d", "MKS SERHAT: writer class already patched")
            return

        _orig_write = cls.write

        def _patched_write(self, stream, nodes, mode=None, **kwargs):
            try:
                from UM.Application import Application as _App2
                gcs = _App2.getInstance().getGlobalContainerStack()
                # Serhat: use MKSPreview.take_screenshot() which has the
                # Snapshot -> backend.getLatestSnapshot fallback chain
                image = MKSPreview.take_screenshot()
                if gcs is not None and image is not None:
                    _simage, _gimage, screenshot_string = MKSPreview.generate_preview(gcs, image)
                    if screenshot_string:
                        Logger.log("d", "MKS SERHAT: injecting preview (%d bytes) via writer patch" % len(screenshot_string))
                        stream.write(screenshot_string)
                        stream.write(";MKSPREVIEWPROCESSED\n")
                        stream.write("; Postprocessed by [MKS WiFi plugin](https://github.com/PrintMakerLab/mks-wifi-plugin)\n")
                        stream.write("; simage=%d\n" % _simage)
                        stream.write("; gimage=%d\n" % _gimage)
                else:
                    Logger.log("d", "MKS SERHAT: skip inject (no gcs=%s or no image=%s)" % (gcs is None, image is None))
            except Exception as e:
                Logger.log("w", "MKS SERHAT: preview injection failed: " + str(e))
            if mode is None:
                return _orig_write(self, stream, nodes, **kwargs)
            return _orig_write(self, stream, nodes, mode, **kwargs)

        cls.write = _patched_write
        cls._serhat_patched = True
        Logger.log("d", "MKS SERHAT: patched %s.write on class" % cls.__name__)
    except Exception as e:
        Logger.log("w", "MKS SERHAT: install patch failed: " + str(e))


@signalemitter
class MKSOutputDevicePlugin(QObject, OutputDevicePlugin):
    def __init__(self):
        super().__init__()
        self.init_translations()
        self._current_printer = None
        self._error_message = None

        Application.getInstance().globalContainerStackChanged.connect(self.on_global_container_stack_changed)

        Application.getInstance().getOutputDeviceManager().writeStarted.connect(MKSPreview.add_preview)

        # Serhat patch: also monkey-patch GCodeWriter as a fallback in case
        # writeStarted -> add_preview's gcode_dict modification is discarded.
        # Do it lazily on first write so all plugins are loaded by then.
        Application.getInstance().getOutputDeviceManager().writeStarted.connect(
            lambda _dev: _serhat_install_gcodewriter_patch())

    _translations = {}
    
    
    def on_global_container_stack_changed(self):
        self.cleanup_old_settings()
        self.mks_current_ip_check()
    
    def cleanup_old_settings(self):
        try:
            Logger.log("d", "Starting clean up old settings.")
            preferences = Application.getInstance().getPreferences()
            # Clean up savepath settings 
            if preferences.getValue("mkswifi/savepath") is not None:
                Logger.log("d", "Clean up savepath.")
                preferences.removePreference("mkswifi/savepath")
                
            # Clean up old manual_instances settings        
            if preferences.getValue("mkswifi/manual_instances") is not None:
                Logger.log("d", "Clean up manual_instances.")
                preferences.removePreference("mkswifi/manual_instances")
                
            # Clean up old autoprint settings
            if preferences.getValue("mkswifi/autoprint") is not None:
                Logger.log("d", "Clean up autoprint.")
                preferences.removePreference("mkswifi/autoprint")
            
            active_machine = Application.getInstance().getGlobalContainerStack()
            if active_machine:
                meta_data = active_machine.getMetaData()                    
                # Clean up old mks_network_key settings
                if "mks_network_key" in meta_data:
                    Logger.log("d", "Clean up mks_network_key.")
                    active_machine.setMetaDataEntry("mks_network_key", None)
                    active_machine.removeMetaDataEntry("mks_network_key")
            Logger.log("d", "Clean up old settings complited.")
        except Exception as e:
            Logger.log("w", "Could not clean up old settings.: "+str(e))

    def init_translations(self):
        self._translations = {
            "connected": catalog.i18nc("@info:status Don't translate the XML tags <message>!", "<message>{0}</message> printer connected successfully!"),
            "disconnected": catalog.i18nc("@info:status Don't translate the XML tags <message>!", "<message>{0}</message> printer disconnected!")
        }

    printerListChanged = Signal()

    def mks_current_ip_check(self):
        Logger.log("d", "mks_current_ip_check called")
        # closing previous printer
        if self._current_printer:
            self.mks_remove_output_device(self._current_printer.getKey())
        # checking new printer got mks_current_ip
        active_machine = Application.getInstance().getGlobalContainerStack()
        if active_machine:
            meta_data = active_machine.getMetaData()
            if meta_data and Constants.CURRENT_IP in meta_data:
                address = active_machine.getMetaDataEntry(Constants.CURRENT_IP)
                self.addPrinter(address)

    def start(self):
        Logger.log("d", "start called")
        # self.startDiscovery()
        self.mks_current_ip_check()
        
    def startDiscovery(self):
        Logger.log("d", "startDiscovery called")

    def addPrinter(self, address):
        Logger.log("d", "addPrinter %s" % (address))
        instance_name = "mks:%s" % address

        active_printer_name = Application.getInstance().getGlobalContainerStack().getName()

        properties = {
            b"name": active_printer_name.encode("utf-8"),
            b"address": address.encode("utf-8"),
            b"manual": b"true",
            b"incomplete": b"false"
        }

        self._current_printer = MKSOutputDevice.MKSOutputDevice(instance_name, address, properties)
        if self._current_printer is None:
            Logger.log("w", "Current printer not found")
        else:
            Logger.log("d", "addPrinter, connecting [%s]..." % self._current_printer.getKey())
            self._current_printer.connect()
            self._current_printer.connectionStateChanged.connect(
                self._onPrinterConnectionStateChanged)

    def mks_remove_output_device(self, key):
        Logger.log("d", "mks_remove_output_device %s" % key)
        if self._current_printer:
            self._current_printer.disconnect()
            self._current_printer.connectionStateChanged.disconnect(self._onPrinterConnectionStateChanged)
            self._current_printer = None
            if self.getOutputDeviceManager().getOutputDevice(key):
                self.getOutputDeviceManager().removeOutputDevice(key)

    def mks_add_printer_to_list(self, address):
        Logger.log("d", "mks_add_printer_to_list %s" % (address))

        active_machine = Application.getInstance().getGlobalContainerStack()
        
        ip_list_entry = active_machine.getMetaDataEntry(Constants.IP_LIST)

        if ip_list_entry:
            ip_list = ip_list_entry.split(",")
            ip_list.append(address)
            active_machine.setMetaDataEntry(Constants.IP_LIST, ','.join(ip_list))
        else:
            active_machine.setMetaDataEntry(Constants.IP_LIST, address)
        self.printerListChanged.emit()

    def mks_remove_printer_from_list(self, address):
        Logger.log("d", "mks_remove_printer_from_list %s" % (address))
        active_machine = Application.getInstance().getGlobalContainerStack()

        if active_machine.getMetaDataEntry(Constants.CURRENT_IP) == self._current_printer:
            active_machine.setMetaDataEntry(Constants.CURRENT_IP, None)
            active_machine.removeMetaDataEntry(Constants.CURRENT_IP)

        if address:
            ip_list = active_machine.getMetaDataEntry(Constants.IP_LIST).split(",")

            ip_list.remove(address)

            if ip_list:
                active_machine.setMetaDataEntry(Constants.IP_LIST, ','.join(ip_list))
            else:
                active_machine.setMetaDataEntry(Constants.IP_LIST, None)
                active_machine.removeMetaDataEntry(Constants.IP_LIST)

        if self._current_printer and self._current_printer.address == address:
            self.mks_remove_output_device(self._current_printer.getKey())
            
        self.printerListChanged.emit()

    def mks_edit_printer_in_list(self, prev_address, address):
        active_machine = Application.getInstance().getGlobalContainerStack()
        if active_machine is not None:
            ip_list_entry = active_machine.getMetaDataEntry(Constants.IP_LIST)
            if ip_list_entry:
                ip_list = ip_list_entry.split(",")
                if prev_address != "":
                    ip_list.remove(prev_address)
                if address != "":
                    ip_list.append(address)
                active_machine.setMetaDataEntry(Constants.IP_LIST, ','.join(ip_list))
            
            self.printerListChanged.emit()

    def getPrinters(self):
        active_machine = Application.getInstance().getGlobalContainerStack()        
        if active_machine is None:
            Logger.log("w", "Active machine not found")
            return []

        ip_list_entry = active_machine.getMetaDataEntry(Constants.IP_LIST)
        if ip_list_entry:
            return ip_list_entry.split(",")
        return []

    def _onPrinterConnectionStateChanged(self, key):
        if self._current_printer is None:
            Logger.log("w", "Current printer not found")
            return

        current_key = self._current_printer.getKey()
        printer_name = self._current_printer._properties.get(b"name", b"").decode("utf-8")
        if current_key != key:
                Logger.log("w", "_current_printer.getKey != %s" % key)

        if self._current_printer.isConnected:
            if self._error_message:
                self._error_message.hide()
            connected = self._translations.get("connected")
            if connected:
                self._error_message = Message(connected.format(printer_name))
                self._error_message.show()
            self.getOutputDeviceManager().addOutputDevice(self._current_printer)
        else:
            if self.getOutputDeviceManager().getOutputDevice(key):
                disconnected = self._translations.get("disconnected")
                if disconnected:
                    self._error_message = Message(disconnected.format(printer_name))
                    self._error_message.show()
                self.getOutputDeviceManager().removeOutputDevice(current_key)

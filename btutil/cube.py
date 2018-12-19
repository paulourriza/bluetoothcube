import kivy
from jnius import autoclass, PythonJavaClass, java_method, cast

GATT_STATE_CONNECTED = 0x02
GATT_STATE_DISCONNECTED = 0x00
GATT_SUCCESS = 0x00

UUID = autoclass('java.util.UUID')

CUBE_STATE_SERVICE = UUID.fromString(
    "0000aadb-0000-1000-8000-00805f9b34fb")
CUBE_STATE_RESPONSE = UUID.fromString(
    "0000aadc-0000-1000-8000-00805f9b34fb")

CUBE_INFO_SERVICE = UUID.fromString(
    "0000aaaa-0000-1000-8000-00805f9b34fb")
CUBE_INFO_RESPONSE = UUID.fromString(
    "0000aaab-0000-1000-8000-00805f9b34fb")
CUBE_INFO_REQUEST = UUID.fromString(
    "0000aaac-0000-1000-8000-00805f9b34fb")


CLIENT_CHARACTERISTIC_UUID = UUID.fromString(
    "00002902-0000-1000-8000-00805f9b34fb")

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothGattDescriptor = autoclass(
    'android.bluetooth.BluetoothGattDescriptor')


def get_app_context():
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
    return cast('android.content.Context',
                currentActivity.getApplicationContext())


# Searches for a bluetooth cube.
class BluetoothCubeScanner(kivy.event.EventDispatcher):
    def __init__(self):
        self.register_event_type('on_cube_found')
        super().__init__()
        self.default_adapter = BluetoothAdapter.getDefaultAdapter()
        self.gatt_callback = None

    class scanCallback(PythonJavaClass):
        __javainterfaces__ = [
            'android/bluetooth/BluetoothAdapter$LeScanCallback']

        def __init__(self, onLeScan_callback):
            super(BluetoothCubeScanner.scanCallback, self).__init__()
            self.onLeScan_callback = onLeScan_callback

        @java_method("(Landroid/bluetooth/BluetoothDevice;I[B)V")
        def onLeScan(self, device, rssi, scanrecord):
            self.onLeScan_callback(device)

    class gattCallback(PythonJavaClass):
        __javainterfaces__ = [
            'org/supercube/BluetoothGattImplem$OnBluetoothGattCallback']
        __javacontext__ = 'app'

        def __init__(self,
                     onConnectionStateChange_callback,
                     onServicesDiscovered_callback,
                     onDescriptorWrite_callback,
                     onCharacteristicChanged_callback):
            super(BluetoothCubeScanner.gattCallback, self).__init__()
            self.onConnectionStateChange_callback = \
                onConnectionStateChange_callback
            self.onServicesDiscovered_callback = \
                onServicesDiscovered_callback
            self.onDescriptorWrite_callback = \
                onDescriptorWrite_callback
            self.onCharacteristicChanged_callback = \
                onCharacteristicChanged_callback

        @java_method('(Landroid/bluetooth/BluetoothGatt;II)V')
        def onConnectionStateChange(self, gatt, status, newstate):
            self.onConnectionStateChange_callback(gatt, status, newstate)

        @java_method('(Landroid/bluetooth/BluetoothGatt;I)V')
        def onServicesDiscovered(self, gatt, status):
            self.onServicesDiscovered_callback(gatt, status)

        @java_method('(Landroid/bluetooth/BluetoothGatt;'
                     'Landroid/bluetooth/BluetoothGattDescriptor;I)V')
        def onDescriptorWrite(self, gatt, descriptor, status):
            self.onDescriptorWrite_callback(gatt, status)

        @java_method('(Landroid/bluetooth/BluetoothGatt;'
                     'Landroid/bluetooth/BluetoothGattCharacteristic;)V')
        def onCharacteristicChanged(self, gatt, characteristic):
            self.onCharacteristicChanged_callback(gatt, characteristic)

    def scan(self):
        self.devices_found = set()
        self.gatt_callback = BluetoothCubeScanner.scanCallback(
            self.on_scan_device_found)
        self.default_adapter.startLeScan(self.gatt_callback)

    def stop_scan(self):
        if self.gatt_callback:
            self.default_adapter.stopLeScan(self.gatt_callback)
        self.gatt_callback = None

    def on_scan_device_found(self, device):
        addr = device.getAddress()
        if addr in self.devices_found:
            return
        self.devices_found.add(addr)

        name = device.getName()
        if name and (name.startswith("GiC") or name.startswith("GiS")):
            self.dispatch('on_cube_found', device)

    def on_cube_found(self, *args):
        pass


class BluetoothCubeConnection(kivy.event.EventDispatcher):
    def __init__(self):
        self.register_event_type('on_cube_connecting')
        self.register_event_type('on_cube_connecting_failed')
        self.register_event_type('on_cube_connected')
        self.register_event_type('on_cube_disconnected')
        self.register_event_type('on_state_updated')
        super().__init__()
        self.gatt = None
        self.connected = False
        self.cube_init_phase = 0

    def connect(self, device):
        app_context = get_app_context()

        self.disconnect()

        pycallback = BluetoothCubeScanner.gattCallback(
            self.on_gatt_connection_state_change,
            self.on_gatt_services_discovered,
            self.on_gatt_descriptor_write,
            self.on_gatt_characteristic_changed
        )
        bg = autoclass('org/supercube/BluetoothGattImplem')()
        bg.setCallback(pycallback)

        self.gatt = device.connectGatt(app_context, False, bg)
        self.connected = False

        self.dispatch('on_cube_connecting',
                      f"Connecting to {device.getName()}...", 20)

    def disconnect(self):
        if self.gatt:
            print("Disconnecting.")
            self.gatt.close()
            self.gatt = None
            self.connected = False

    def on_gatt_connection_state_change(self, gatt, status, newstate):
        print(f"Gatt state changed: {newstate}")
        if newstate == GATT_STATE_CONNECTED:
            print("Connected!")
            self.connected = True
            self.dispatch('on_cube_connecting',
                          "Initializing cube...", 55)
            self.gatt.discoverServices()
        if newstate == GATT_STATE_DISCONNECTED:
            print("Disconnected.")
            self.disconnect()
            if self.connected:  # There was an active connection
                self.dispatch('on_cube_disconnected')
            else:
                self.dispatch('on_cube_connecting_failed',
                              "Connection failed.")

    def on_gatt_services_discovered(self, gatt, status):
        print(f"Service discovery: {status}")
        if status == GATT_SUCCESS:
            self.dispatch('on_cube_connecting',
                          "Setting up communication...", 85)
            self.enable_notifications()

    def on_gatt_descriptor_write(self, gatt, descriptor, status):
        print("Desc write!")

    def on_gatt_characteristic_changed(self, gatt, characteristic):
        if characteristic.equals(self.state_response_characteristic):
            self.dispatch('on_state_updated', characteristic.getValue())
        else:
            print(f"Characteristic {characteristic.getUuid()} changed!")

    def enable_notifications(self):
        # BluetoothGattService
        self.cube_state_service = self.gatt.getService(CUBE_STATE_SERVICE)
        if not self.cube_state_service:
            print("Cube status service not found")
            self.disconnect()
            self.dispatch('on_cube_connecting_failed',
                          "Status service not found.")
            return

        # BluetoothGattService
        self.cube_info_service = self.gatt.getService(CUBE_INFO_SERVICE)
        if not self.cube_info_service:
            print("Cube info service not found")
            self.disconnect()
            self.dispatch('on_cube_connecting_failed',
                          "Info service not found.")
            return

        # BluetoothGattCharacteristic
        self.state_response_characteristic = \
            self.cube_state_service.getCharacteristic(CUBE_STATE_RESPONSE)
        self.info_response_characteristic = \
            self.cube_info_service.getCharacteristic(CUBE_INFO_REQUEST)
        self.info_response_characteristic = \
            self.cube_info_service.getCharacteristic(CUBE_INFO_RESPONSE)
        if not self.state_response_characteristic \
           or not self.info_response_characteristic \
           or not self.info_response_characteristic:
            print("Cube characteristics not found")
            self.disconnect()
            self.dispatch('on_cube_connecting_failed',
                          "Characteristics not found.")
            return

        # Enable notifications on cube state characteristic.
        # When we enable notifications, the onCharacteristicChanged
        # callback will get triggered on characteristic change.
        if not self.gatt.setCharacteristicNotification(
                self.state_response_characteristic, True):
            print("Could not enable notifications")
            self.disconnect()
            self.dispatch('on_cube_connecting_failed',
                          "Failed to enable state notifications.")
            return

        if not self.gatt.setCharacteristicNotification(
                self.info_response_characteristic, True):
            print("Could not enable info response notifications")
            self.disconnect()
            self.dispatch('on_cube_connecting_failed',
                          "Failed to enable info notifications.")
            return

        # Enable notifications on these particular descriptor.
        state = self.state_response_characteristic.getDescriptor(
            CLIENT_CHARACTERISTIC_UUID)
        state.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        self.gatt.writeDescriptor(state)
        info = self.info_response_characteristic.getDescriptor(
            CLIENT_CHARACTERISTIC_UUID)
        info.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        self.gatt.writeDescriptor(info)

        self.dispatch('on_cube_connected')

    def on_cube_connecting(self, *args):
        pass

    def on_cube_connecting_failed(self, *args):
        pass

    def on_cube_connected(self, *args):
        pass

    def on_cube_disconnected(self, *args):
        pass

    def on_state_updated(self, *args):
        pass
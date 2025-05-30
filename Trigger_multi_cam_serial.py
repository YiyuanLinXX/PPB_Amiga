import os
import PySpin
import sys
import atexit
import argparse
import time
import serial
import numpy as np

class TriggerType:
    SOFTWARE = 1
    HARDWARE = 2

CHOSEN_TRIGGER = TriggerType.SOFTWARE
AUTO_EXPOSURE = True

trigger_delay_to_set = 45.
exposure_time_to_set = 500.
gain_to_set = 5.
wb_red = 1.34
wb_blue = 2.98
second_per_frame = 0.5



def configure_white_balance(cam):
    global wb_red
    global wb_blue
    print('*** CONFIGURING white balance ***\n')

    try:
        result = True
        nodemap = cam.GetNodeMap()
        node_wb = PySpin.CEnumerationPtr(nodemap.GetNode('BalanceWhiteAuto'))
        if not PySpin.IsAvailable(node_wb) or not PySpin.IsReadable(node_wb):
            print('Unable to disable auto wb (node retrieval). Aborting...')
            return False

        node_wb_off = node_wb.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_wb_off) or not PySpin.IsReadable(node_wb_off):
            print('Unable to disable auto wb (enum entry retrieval). Aborting...')
            return False

        node_wb.SetIntValue(node_wb_off.GetValue())
        print('Automatic WB disabled...')

        node_wb_selector = PySpin.CEnumerationPtr(nodemap.GetNode('BalanceRatioSelector'))
        print(PySpin.IsWritable(node_wb_selector))
        node_wb_red = node_wb_selector.GetEntryByName('Red')
        node_wb_selector.SetIntValue(node_wb_red.GetValue())
        node_wb_ratio = PySpin.CFloatPtr(nodemap.GetNode('BalanceRatio'))
        node_wb_ratio.SetValue(wb_red)

        node_wb_blue = node_wb_selector.GetEntryByName('Blue')
        node_wb_selector.SetIntValue(node_wb_blue.GetValue())
        node_wb_ratio = PySpin.CFloatPtr(nodemap.GetNode('BalanceRatio'))
        node_wb_ratio.SetValue(wb_blue)
        


        print('WB set')

    except Exception as ex:
        print('Error: %s' % ex)
        result = False
    return result

def reset_white_balance(cam):
    """
    This function returns the camera to a normal state by re-enabling automatic exposure.

    :param cam: Camera to reset exposure on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True
        nodemap = cam.GetNodeMap()
        node_wb = PySpin.CEnumerationPtr(nodemap.GetNode('BalanceWhiteAuto'))
        if not PySpin.IsAvailable(node_wb) or not PySpin.IsReadable(node_wb):
            print('Unable to disable auto wb (node retrieval). Aborting...')
            return False

        node_wb_on = node_wb.GetEntryByName('On')
        if not PySpin.IsAvailable(node_wb_on) or not PySpin.IsReadable(node_wb_on):
            print('Unable to disable auto wb (enum entry retrieval). Aborting...')
            return False

        node_wb.SetIntValue(node_wb_on.GetValue())
        print('Automatic WB enabled...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result





def configure_gain(cam):
    global gain_to_set
    print('*** CONFIGURING GAIN ***\n')

    try:
        result = True

        if cam.GainAuto.GetAccessMode() != PySpin.RW:
            print('Unable to disable automatic gain. Aborting...')
            return False

        cam.GainAuto.SetValue(PySpin.GainAuto_Off)
        print('Automatic gain disabled...')

        if cam.Gain.GetAccessMode() != PySpin.RW:
            print('Unable to set gain. Aborting...')
            return False

        gain_to_set = min(cam.Gain.GetMax(), gain_to_set)
        cam.Gain.SetValue(gain_to_set)
        print('Gain set to %s us...\n' % gain_to_set)

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result

def reset_gain(cam):
    try:
        result = True

        if cam.GainAuto.GetAccessMode() != PySpin.RW:
            print('Unable to enable automatic gain (node retrieval). Non-fatal error...')
            return False

        cam.GainAuto.SetValue(PySpin.GainAuto_Continuous)

        print('Automatic gain enabled...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def configure_exposure(cam):
    """
     This function configures a custom exposure time. Automatic exposure is turned
     off in order to allow for the customization, and then the custom setting is
     applied.

     :param cam: Camera to configure exposure for.
     :type cam: CameraPtr
     :return: True if successful, False otherwise.
     :rtype: bool
    """
    global exposure_time_to_set
    print('*** CONFIGURING EXPOSURE ***\n')

    try:
        result = True

        # Turn off automatic exposure mode
        #
        # *** NOTES ***
        # Automatic exposure prevents the manual configuration of exposure
        # times and needs to be turned off for this example. Enumerations
        # representing entry nodes have been added to QuickSpin. This allows
        # for the much easier setting of enumeration nodes to new values.
        #
        # The naming convention of QuickSpin enums is the name of the
        # enumeration node followed by an underscore and the symbolic of
        # the entry node. Selecting "Off" on the "ExposureAuto" node is
        # thus named "ExposureAuto_Off".
        #
        # *** LATER ***
        # Exposure time can be set automatically or manually as needed. This
        # example turns automatic exposure off to set it manually and back
        # on to return the camera to its default state.

        if cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to disable automatic exposure. Aborting...')
            return False

        cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        print('Automatic exposure disabled...')

        # Set exposure time manually; exposure time recorded in microseconds
        #
        # *** NOTES ***
        # Notice that the node is checked for availability and writability
        # prior to the setting of the node. In QuickSpin, availability and
        # writability are ensured by checking the access mode.
        #
        # Further, it is ensured that the desired exposure time does not exceed
        # the maximum. Exposure time is counted in microseconds - this can be
        # found out either by retrieving the unit with the GetUnit() method or
        # by checking SpinView.

        if cam.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to set exposure time. Aborting...')
            return False

        # Ensure desired exposure time does not exceed the maximum
        #exposure_time_to_set = 200.0
        exposure_time_to_set = min(cam.ExposureTime.GetMax(), exposure_time_to_set)
        cam.ExposureTime.SetValue(exposure_time_to_set)
        print('Shutter time set to %s us...\n' % exposure_time_to_set)

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def reset_exposure(cam):
    """
    This function returns the camera to a normal state by re-enabling automatic exposure.

    :param cam: Camera to reset exposure on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Turn automatic exposure back on
        #
        # *** NOTES ***
        # Automatic exposure is turned on in order to return the camera to its
        # default state.

        if cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to enable automatic exposure (node retrieval). Non-fatal error...')
            return False

        cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

        print('Automatic exposure enabled...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result

def configure_trigger(cam):
    """
    This function configures the camera to use a trigger. First, trigger mode is
    set to off in order to select the trigger source. Once the trigger source
    has been selected, trigger mode is then enabled, which has the camera
    capture only a single image upon the execution of the chosen trigger.

     :param cam: Camera to configure trigger for.
     :type cam: CameraPtr
     :return: True if successful, False otherwise.
     :rtype: bool
    """

    global trigger_delay_to_set
    result = True

    print('*** CONFIGURING TRIGGER ***\n')
    print('Note that if the application / user software triggers faster than frame time, the trigger may be dropped / skipped by the camera.\n')

    if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
        print('Software trigger chosen ...')
    elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
        print('Hardware trigger chose ...')

    try:
        # Ensure trigger mode off
        # The trigger must be disabled in order to configure whether the source
        # is software or hardware.
        nodemap = cam.GetNodeMap()
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            print('Unable to disable trigger mode (node retrieval). Aborting...')
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

        print('Trigger mode disabled...')
        
        # Set TriggerSelector to FrameStart
        # For this example, the trigger selector should be set to frame start.
        # This is the default for most cameras.
        node_trigger_selector= PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSelector'))

        if not PySpin.IsAvailable(node_trigger_selector) or not PySpin.IsWritable(node_trigger_selector):
            print('Unable to get trigger selector (node retrieval). Aborting...')
            return False

        node_trigger_selector_framestart = node_trigger_selector.GetEntryByName('FrameStart')
        if not PySpin.IsAvailable(node_trigger_selector_framestart) or not PySpin.IsReadable(
                node_trigger_selector_framestart):
            print('Unable to set trigger selector (enum entry retrieval). Aborting...')
            return False
        node_trigger_selector.SetIntValue(node_trigger_selector_framestart.GetValue())
        
        print('Trigger selector set to frame start...')

        cam.TriggerDelay.SetValue(trigger_delay_to_set)
        print('Trigger delay set')

        # Select trigger source
        # The trigger source must be set to hardware or software while trigger
        # mode is off.
        node_trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
        
        if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
            node_trigger_source_software = node_trigger_source.GetEntryByName('Software')
            if not PySpin.IsAvailable(node_trigger_source_software) or not PySpin.IsReadable(
                    node_trigger_source_software):
                print('Unable to set trigger source (enum entry retrieval). Aborting...')
                return False
            node_trigger_source.SetIntValue(node_trigger_source_software.GetValue())
            print('Trigger source set to software...')

        elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
            node_trigger_source_hardware = node_trigger_source.GetEntryByName('Line0')

            if not PySpin.IsAvailable(node_trigger_source_hardware) or not PySpin.IsReadable(
                    node_trigger_source_hardware):
                print('Unable to set trigger source (enum entry retrieval). Aborting...')
                return False
            node_trigger_source.SetIntValue(node_trigger_source_hardware.GetValue())
            
            node_trigger_activation = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerActivation'))
            if not PySpin.IsAvailable(node_trigger_activation) or not PySpin.IsWritable(node_trigger_activation):
                print('Unable to get trigger activation (node retrieval). Aborting...')
                return False
            node_trigger_activation_risingedge = node_trigger_activation.GetEntryByName('RisingEdge')

            if not PySpin.IsAvailable(node_trigger_activation_risingedge) or not PySpin.IsReadable(node_trigger_activation_risingedge):
                print('Unable to set trigger activation (enum entry retrieval). Aborting...')
                return False
            node_trigger_activation.SetIntValue(node_trigger_activation_risingedge.GetValue())

            print('Trigger source set to hardware...')

        # Turn trigger mode on
        # Once the appropriate trigger source has been set, turn trigger mode
        # on in order to retrieve images using the trigger.
        node_trigger_mode_on = node_trigger_mode.GetEntryByName('On')
        if not PySpin.IsAvailable(node_trigger_mode_on) or not PySpin.IsReadable(node_trigger_mode_on):
            print('Unable to enable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_on.GetValue())
        print('Trigger mode turned back on...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result



def reset_trigger(nodemap):
    """
    This function returns the camera to a normal state by turning off trigger mode.
  
    :param nodemap: Transport layer device nodemap.
    :type nodemap: INodeMap
    :returns: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True
        node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
        if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
            print('Unable to disable trigger mode (node retrieval). Aborting...')
            return False

        node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
        if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
            print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
            return False

        node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())

        print('Trigger mode disabled...')

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def grab_next_image_by_trigger(cam_list,ser):
    """
    This function acquires an image by executing the trigger node.

    :param cam: Camera to acquire images from.
    :param nodemap: Device nodemap.
    :type cam: CameraPtr
    :type nodemap: INodeMap
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True
        # Use trigger to capture image
        # The software trigger only feigns being executed by the Enter key;
        # what might not be immediately apparent is that there is not a
        # continuous stream of images being captured; in other examples that
        # acquire images, the camera captures a continuous stream of images.
        # When an image is retrieved, it is plucked from the stream.

        if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
            for cam in cam_list:
                nodemap = cam.GetNodeMap()
                node_softwaretrigger_cmd = PySpin.CCommandPtr(nodemap.GetNode('TriggerSoftware'))
                if not PySpin.IsAvailable(node_softwaretrigger_cmd) or not PySpin.IsWritable(node_softwaretrigger_cmd):
                    print('Unable to execute trigger. Aborting...')
                    return False

                node_softwaretrigger_cmd.Execute()

        elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
            print('Use the hardware to trigger image acquisition.')
            startTrigger(ser)
        triggerTime = time.time()
    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result,triggerTime
    

def startTrigger(ser):
    print('start trigger...')
    ser.write(b's\n')
    
    
def stopTrigger(ser):
    print('stop trigger...')
    ser.write(b'e\n')


def acquire_images(cam_list,dataPath,ser):
    """
    :param cam_list: List of cameras
    :type cam_list: CameraList
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    imgOption = PySpin.PNGOption()
    imgOption.compressionLevel=0
    global second_per_frame

    print('*** IMAGE ACQUISITION ***\n')
    try:
        result = True

        # Prepare each camera to acquire images
        #
        # *** NOTES ***
        # For pseudo-simultaneous streaming, each camera is prepared as if it
        # were just one, but in a loop. Notice that cameras are selected with
        # an index. We demonstrate pseduo-simultaneous streaming because true
        # simultaneous streaming would require multiple process or threads,
        # which is too complex for an example.
        #

        for i, cam in enumerate(cam_list):

            # Set acquisition mode to continuous
            node_acquisition_mode = PySpin.CEnumerationPtr(cam.GetNodeMap().GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (node retrieval; camera %d). Aborting... \n' % i)
                return False

            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry \'continuous\' retrieval %d). \
                Aborting... \n' % i)
                return False

            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()

            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            print('Camera %d acquisition mode set to continuous...' % i)

            # Begin acquiring images
            cam.BeginAcquisition()

            print('Camera %d started acquiring images...' % i)

            print()

        # Retrieve, convert, and save images for each camera
        #
        # *** NOTES ***
        # In order to work with simultaneous camera streams, nested loops are
        # needed. It is important that the inner loop be the one iterating
        # through the cameras; otherwise, all images will be grabbed from a
        # single camera before grabbing any images from another.

        # Create ImageProcessor instance for post processing images
        processor = PySpin.ImageProcessor()

        # Set default image processor color processing method
        #
        # *** NOTES ***
        # By default, if no specific color processing algorithm is set, the image
        # processor will default to NEAREST_NEIGHBOR method.
        processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)

        n = 0
        numBroken = 0
        overTimeCounter = 0
        starttime = time.time()
        
        while True:
            starttime2 = time.time()
            try:
                result,triggerTime = grab_next_image_by_trigger(cam_list,ser)
                # if CHOSEN_TRIGGER == TriggerType.HARDWARE:
                #     time.sleep(0.001)
                #     stopTrigger(ser)
                
                for i, cam in enumerate(cam_list):
                    try:
                        # Retrieve device serial number for filename
                        node_device_serial_number = PySpin.CStringPtr(cam.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))

                        if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
                            device_serial_number = node_device_serial_number.GetValue()

                        # Retrieve next received image and ensure image completion
                        image_result = cam.GetNextImage(5000)

                        if image_result.IsIncomplete():
                            print('Image incomplete with image status %d ... \n' % image_result.GetImageStatus())
                            numBroken = numBroken + 1
                        else:
                            received_time = triggerTime*10**6
   
                            # Convert image to RGB8
                            image_converted = processor.Convert(image_result, PySpin.PixelFormat_RGB8)#, PySpin.HQ_LINEAR)

                            # Create a unique filename
                            if device_serial_number:
                                camPath = dataPath + '%s/' % (device_serial_number)
                                if not os.path.exists(camPath):
                                        os.makedirs(camPath)
                                filename = camPath + '%d_%d.jpg' % (n,received_time) 
                            else:
                                #filename = dataPath + 'AcquisitionMultipleCamera-%d-%d.jpg' % (i, n)
                                filename = dataPath + 'AcquisitionMultipleCamera-%d-%d.jpg' % (i, received_time)

                            # Save image
                            image_converted.Save(filename)
                            print('Image saved at %s' % filename)
                            print('Broken images: %s' % numBroken)
                            print('Over time: %s' % overTimeCounter)

                        # Release image
                        image_result.Release()
                        print()

                    except Exception as ex:
                        print('Error: %s' % ex)
                        result = False

                n = n + 1
                print('Time: %s' % (time.time()-starttime2))
                if (time.time()-starttime2) > second_per_frame:
                    overTimeCounter += 1
                time.sleep(second_per_frame-((time.time()-starttime)%second_per_frame))
 
            except KeyboardInterrupt:
                print("catched interrupt")
                break

        # End acquisition for each camera
        #
        # *** NOTES ***
        # Notice that what is usually a one-step process is now two steps
        # because of the additional step of selecting the camera. It is worth
        # repeating that camera selection needs to be done once per loop.
        #
        # It is possible to interact with cameras through the camera list with
        # GetByIndex(); this is an alternative to retrieving cameras as
        # CameraPtr objects that can be quick and easy for small tasks.
        for cam in cam_list:

            # End acquisition
            cam.EndAcquisition()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result

def print_device_info(nodemap, cam_num):
    """
    This function prints the device information of the camera from the transport
    layer; please see NodeMapInfo example for more in-depth comments on printing
    device information from the nodemap.

    :param nodemap: Transport layer device nodemap.
    :param cam_num: Camera number.
    :type nodemap: INodeMap
    :type cam_num: int
    :returns: True if successful, False otherwise.
    :rtype: bool
    """

    print('Printing device information for camera %d... \n' % cam_num)

    try:
        result = True
        node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))

        if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
            features = node_device_information.GetFeatures()
            for feature in features:
                node_feature = PySpin.CValuePtr(feature)
                print('%s: %s' % (node_feature.GetName(),
                                  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))

        else:
            print('Device control information not available.')
        print()

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result

def run_multiple_cameras(cam_list,dataPath,ser):
    """
    This function acts as the body of the example; please see NodeMapInfo example
    for more in-depth comments on setting up cameras.

    :param cam_list: List of cameras
    :type cam_list: CameraList
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    try:
        result = True

        # Retrieve transport layer nodemaps and print device information for
        # each camera
        # *** NOTES ***
        # This example retrieves information from the transport layer nodemap
        # twice: once to print device information and once to grab the device
        # serial number. Rather than caching the nodem#ap, each nodemap is
        # retrieved both times as needed.
        print('*** DEVICE INFORMATION ***\n')

        for i, cam in enumerate(cam_list):

            # Retrieve TL device nodemap
            nodemap_tldevice = cam.GetTLDeviceNodeMap()

            # Print device information
            result &= print_device_info(nodemap_tldevice, i)

        # Initialize each camera
        #
        # *** NOTES ***
        # You may notice that the steps in this function have more loops with
        # less steps per loop; this contrasts the AcquireImages() function
        # which has less loops but more steps per loop. This is done for
        # demonstrative purposes as both work equally well.
        #
        # *** LATER ***
        # Each camera needs to be deinitialized once all images have been
        # acquired.
        for i, cam in enumerate(cam_list):

            # Initialize camera
            cam.Init()

            if configure_trigger(cam) is False: #or configure_Packet(cam) is False:
                return False
            if AUTO_EXPOSURE:
                if not (reset_exposure(cam) and reset_gain(cam)):
                    return False
            else:
                # Configure exposure  
                if not (configure_exposure(cam) and configure_gain(cam) and configure_white_balance(cam)):
                    return False


        # Acquire images on all cameras
        result &= acquire_images(cam_list,dataPath,ser)

        # Deinitialize each camera
        #
        # *** NOTES ***
        # Again, each camera must be deinitialized separately by first
        # selecting the camera and then deinitializing it.
        for cam in cam_list:

            # Deinitialize camera

            # Reset trigger
            nodemap = cam.GetNodeMap()
            result &= reset_trigger(nodemap)

            # Reset exposure
            result &= reset_exposure(cam)
            result &= reset_gain(cam)
            result &= reset_white_balance(cam)
            cam.DeInit()

            # Release reference to camera
            # NOTE: Unlike the C++ examples, we cannot rely on pointer objects being automatically
            # cleaned up when going out of scope.
            # The usage of del is preferred to assigning the variable to None.
            del cam

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result


def main():
    """
    :return: True if successful, False otherwise.
    :rtype: bool
    """

    # we must ensure that we have permission to write to this folder.
    # If we do not have permission, fail right away.
    global CHOSEN_TRIGGER
    global AUTO_EXPOSURE
    parser = argparse.ArgumentParser(description='get output dir')
    parser.add_argument('output_dir',type = str)
    parser.add_argument('trigger',type = int)
    parser.add_argument('auto_exposure',type = int)
    args = parser.parse_args()
    

    ser = serial.Serial('/dev/ttyACM0', 9600)  #serial
    ser.close()
    ser.open()


    CHOSEN_TRIGGER = TriggerType.SOFTWARE
    if args.trigger == 0:
        CHOSEN_TRIGGER = TriggerType.HARDWARE
    else:
        CHOSEN_TRIGGER = TriggerType.SOFTWARE
    AUTO_EXPOSURE = args.auto_exposure == 1

    dataPath = args.output_dir+'/'

    if os.path.exists(dataPath):
        print('folder exists')
        return False
    os.mkdir(dataPath)

    try:
        test_file = open(dataPath+'test.txt', 'w+')
    except IOError:
        print('Unable to write to current directory. Please check permissions.')
        input('Press Enter to exit...')
        return False

    test_file.close()
    os.remove(test_file.name)

    result = True

    # Retrieve singleton reference to system object
    system = PySpin.System.GetInstance()

    # Get current library version
    version = system.GetLibraryVersion()
    print('Library version: %d.%d.%d.%d' % (version.major, version.minor, version.type, version.build))

    # Retrieve list of cameras from the system
    cam_list = system.GetCameras()

    num_cameras = cam_list.GetSize()

    print('Number of cameras detected: %d' % num_cameras)

    # Finish if there are no cameras
    if num_cameras == 0:
        cam_list.Clear()
        system.ReleaseInstance()

        print('Not enough cameras!')
        input('Done! Press Enter to exit...')
        return False

    result = run_multiple_cameras(cam_list,dataPath,ser)

    if args.trigger == 0:
        stopTrigger(ser)

    cam_list.Clear()
    system.ReleaseInstance()


    input('Done! Press Enter to exit...')
    return result

def exit_handler():
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout = 0)  #serial
    ser.close()
    ser.open()
    if CHOSEN_TRIGGER == TriggerType.HARDWARE:
        stopTrigger(ser)


if __name__ == '__main__':
    atexit.register(exit_handler)
    try:
        if main():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)

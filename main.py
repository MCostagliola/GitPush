import customtkinter as ctk
from tkinter import filedialog
from plantcv import plantcv as pcv
from plantcv.parallel import WorkflowInputs
import time
import numpy as np
import os
import imageio.v2 as imageio
import time
import xlsxwriter
import shutil
from natsort import natsorted
import sys
from numba import njit

root = ctk.CTk()

def run_program(path):

    if batch_trigger == False:
        folder_path = path_var.get()
    
    elif batch_trigger == True:
        folder_path = path

    extensions = ('.jpg', '.png')
    def ProcessImagesToBinary(inDirectoryPath) -> str:

        outDirectoryPath = os.path.join(inDirectoryPath, 'processed_images').replace("/", "\\")
        os.makedirs(outDirectoryPath, exist_ok=True)
        print(f'In Path: {inDirectoryPath}\nOut Path: {outDirectoryPath}')
        image_files = pcv.io.read_dataset(inDirectoryPath)

        for img_path in image_files:

            ext = os.path.splitext(img_path)[-1].lower()
            if ext in extensions:
                # Process each image as before
                args = WorkflowInputs(
                    images=[img_path],
                    names=img_path,
                    result=rf'yikes',
                    outdir=rf'{outDirectoryPath}',
                    writeimg=True,
                    debug='none',
                    sample_label=''
                )

                # Debug Params
                pcv.params.debug = args.debug
                img, filename, path = pcv.readimage(filename=img_path)

                # Image Processing - example operations
                a_gray = pcv.rgb2gray_lab(rgb_img=img, channel='a')
                bin_mask = pcv.threshold.otsu(gray_img=a_gray, object_type='dark')
                clean_mask = pcv.closing(gray_img=bin_mask)

                filename = os.path.basename(img_path)
                pcv.print_image(clean_mask, rf'{outDirectoryPath}\{filename}')

        return outDirectoryPath

    @njit
    def formatCellInfoFromFilename(filename):
        """
        Extracts the information from the filename to create a clear and more presentable string.

        :param filename: for the current photo, expected to be in the following format: 06-29-2023_13-52-Rep1.jpg
        :return: formatted string with extracted data, ex: 07/08/2023 09:33AM
        """

        try:

            shortenedname = filename.split("-Rep")[0]
            timeinfo = time.strptime(shortenedname, "%m-%d-%Y_%H-%M")  # struct as defined in time module
            return time.strftime("%m/%d/%Y %I:%M%p", timeinfo)
        except:
            # formatted name could not be parsed, use filename instead
            return filename

    @njit
    def writeData(row, col, filename, newPic, oldPic=None):
        """
        Outputs data for a specific plant and rep to the excel sheet.

        :param row: uppermost row of cell range where work is being written
        :param col: leftmost column of cell range where work is being written
        :param filename: name of the file, containing information to extract for cells
        :param newPic: the matrix representation of green pixels for the current plant
        :param oldPic: the matrix representation of green pixels for the previous plant,
            set to None in the case of the first plant
        :return: nothing
        """

        # Writes the rep number
        Size_Worksheet.write(row, col, row - 1)
        Motion_Worksheet.write(row, col, row - 1)

        # Writes the date and time in a more readable format
        Size_Worksheet.write(row, col + 1, formatCellInfoFromFilename(filename))
        Size_Worksheet.set_column(col + 1, col + 1,
                                len(filename))  # Sets col width to fit width of filename, TODO: refactor to use only once...
        Motion_Worksheet.write(row, col + 1, formatCellInfoFromFilename(filename))
        Motion_Worksheet.set_column(col + 1, col + 1, len(filename))

        # writes the Size value for all plants
        Size_Worksheet.write(row, col + 2, np.count_nonzero(newPic))

        # writes the growth and motion values for all plants aside from the first
        if oldPic is None:
            # N/A when there is no previous data to calculate with
            Motion_Worksheet.write(row, col + 2, "N/A")
        else:
            # Counts the number of pixels (under mask) different from previous capture. Done by XOR operation on image matrices
            Motion_Worksheet.write(row, col + 2, np.count_nonzero(newPic ^ oldPic))
            # Counts the difference in pixels between the new capture and the previous capture.


    ###########################
    ## START OF MAIN PROCEDURE
    ###########################
    temp_time = time.time()

    # stores the desired Excel save name
    savename = "MotionSize"
    # creates the workbook file w/ savename
    workbook = xlsxwriter.Workbook(savename + '.xlsx')

    inDirectoryPath = ProcessImagesToBinary(folder_path)
    os.chdir(folder_path)

    headerformat = workbook.add_format({
        "bold": 1,
        "border": 1,
        "align": "center",
        "valign": "vcenter",
        "fg_color": "yellow",
    })

    #start = time.time()

    pixelsPerPic = 0 # Set after first pic is collected tuple of dimensions (x, y, z = 3)

    Motion_Worksheet = workbook.add_worksheet("Motion_Worksheet")
    Size_Worksheet = workbook.add_worksheet("Size_Worksheet")

    row = 0
    col = 0
    total_picture_count = 0

    oldPic = None  # referenced when determining if we should skip the comparison calculation (for first plant of batch)

    directory = inDirectoryPath
    # Adding headers for Size_Worksheet and Motion_Worksheet
    Size_Worksheet.merge_range(row, col, row, col + 2, directory, headerformat)
    Size_Worksheet.write(row + 1, col, "Num", headerformat)
    Size_Worksheet.write(row + 1, col + 1, "Time", headerformat)
    Size_Worksheet.write(row + 1, col + 2, "Green", headerformat)

    Motion_Worksheet.merge_range(row, col, row, col + 2, directory, headerformat)
    Motion_Worksheet.write(row + 1, col, "Num", headerformat)
    Motion_Worksheet.write(row + 1, col + 1, "Time", headerformat)
    Motion_Worksheet.write(row + 1, col + 2, "Motion", headerformat)

    # Set a fixed column width for the 'Time' column
    Size_Worksheet.set_column(col + 1, col + 1, 20)
    Motion_Worksheet.set_column(col + 1, col + 1, 20)

    row += 2
    # cycle for each image in the folder
    for file in (os.listdir(inDirectoryPath)):

        total_picture_count += 1
        try:

            newPic = imageio.imread(os.path.join(inDirectoryPath, file))
            if newPic is not None:

                # Set pixelsPerPic, only do this for the first pic
                if pixelsPerPic == 0:

                    pixelsPerPic = newPic.shape[0] * newPic.shape[1]  # newPic.shape is a tuple of (height, width, 3(RGB))

                # take out first line below to test speed change
                newIsolatedImage = newPic

                # only evaluates for non-black images in processing
                if np.count_nonzero(newIsolatedImage) > 500:

                    # when reading the first picture, prevents a comparison
                    # attempt with another picture
                    if oldPic is None:

                        writeData(row, col, file, newIsolatedImage)
                    else:

                        writeData(row, col, file, newIsolatedImage, oldIsolatedImage)

                    # add in to test speed change
                    oldIsolatedImage = newIsolatedImage

                    row += 1
                    oldPic = newPic
            else:

                pass
        except Exception as e:

            pass

    # Add chart for Motion_Worksheet
    chart_motion = workbook.add_chart({'type': 'line'}) # Configure type of chart for motion
    chart_motion.set_title({'name': 'Plant Motion Over Time'})
    chart_motion.set_legend({'position': 'none'})

    # Configure the series of the chart from Motion_Worksheet
    chart_motion.add_series({
        'name': '=Motion_Worksheet!$C$1',
        'categories': '=Motion_Worksheet!$B$3:$B$' + str(row),
        'values': '=Motion_Worksheet!$C$3:$C$' + str(row),
        'line': {'width': 1},
    })

    chart_motion.set_x_axis({
        'name': 'Capture Date',
        'name_font': {'size': 18, 'bold': True},
        'date_axis': True,  # Set the x-axis as a date axis
        'major_unit': 12,  # Specify the interval count (display every 2 days, for example)
    })

    chart_motion.set_y_axis({
        'name': 'Pixel Fluctuaton',
        'name_font': {'size': 18, 'bold': True},
    })

    # Insert the chart into the worksheet
    Motion_Worksheet.insert_chart('D2', chart_motion, {'x_scale': 2, 'y_scale': 1.5}) # x_scale & y_scale control size of chart
    # Chart Size can be specificed to a resolution by: {'width': 1920, 'height': 1080}, and then adjusted as needed

    # Add chart for Size_Worksheet
    chart_size = workbook.add_chart({'type': 'line'}) # Configure type of chart for size
    chart_size.set_title({'name': 'Plant Size Over Time'})
    chart_size.set_legend({'position': 'none'})

    # Configure the series of the chart from Size_Worksheet
    chart_size.add_series({
        'name': '=Size_Worksheet!$C$1',
        'categories': '=Size_Worksheet!$B$3:$B$' + str(row),
        'values': '=Size_Worksheet!$C$3:$C$' + str(row),
        'line': {'width': 1},
    })

    chart_size.set_x_axis({
        'name': 'Capture Date',
        'name_font': {'size': 18, 'bold': True},
        'date_axis': True,  # Set the x-axis as a date axis
        'major_unit': 12,  # Specify the interval count (display every 2 days, for example)
    })

    chart_size.set_y_axis({
        'name': 'Pixel Count',
        'name_font': {'size': 18, 'bold': True},
    })

    # Insert the chart into the worksheet
    Size_Worksheet.insert_chart('D2', chart_size, {'x_scale': 2, 'y_scale': 1.5}) # x_scale & y_scale control size of chart
    # Chart Size can be specificed to a resolution by: {'width': 1920, 'height': 1080}, and then adjusted as needed

    workbook.close()
    #easygui.msgbox(f'Processed {total_picture_count} images in {"%0.2f" %(time.time() - start)} seconds')

    if save_images == False:
        shutil.rmtree(inDirectoryPath)

    print(f'Process Time: {"%0.6f" % (time.time() - temp_time)}\nTotal Time: {"%0.6f" % (time.time()-start)}')

#########################
#~~~~~~~~Widgets~~~~~~~~#
#########################

class DebugWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Debug Window")
    
        self.text_widget = ctk.CTkTextbox(self, wrap='word')
        self.text_widget.pack(fill='both', expand=True)
        
        # Redirect stdout to the text widget
        sys.stdout = self
    
    def write(self, message):
        self.text_widget.insert(ctk.END, message)
        self.text_widget.see(ctk.END)
        self.update_idletasks()  
    
    def flush(self):
        pass  # Override flush method to do nothing

    def clear(self):
        self.text_widget.delete('1.0', ctk.END)
    
    def close(self):
        sys.stdout = sys.__stdout__  # Restore original stdout
        self.destroy()


# Globals
save_images = False
batch_trigger = False


def save_image_trigger():

    global save_images

    if save_images:
        save_images = False
    else:
        save_images = True
    return save_images


def trigger_batch_status():

    global batch_trigger

    if batch_trigger:
        batch_trigger = False
    else:
        batch_trigger = True
    return batch_trigger


def choose_folder():

    folder_path = filedialog.askdirectory()
    path_var.set(folder_path)

@njit
def show_message(message):
    top = ctk.CTkToplevel()

    # Calculate screen dimensions
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()
    
    # Calculate window dimensions and position to center it on the screen
    width = 450
    height = 200
    x = (screen_width + width) // 2
    y = (screen_height + height - 450) // 1
    
    top.geometry(f"{width}x{height}+{x}+{y}")  # Set geometry to center the window
    top.focus()  # Ensure the window gets focus

    top.title("Processing Information")
    label = ctk.CTkLabel(top, text=message, width=200, height=200, anchor='center')
    label.pack(padx=0, pady=0)
    

def batch():
    global start
    start = time.time()
    if batch_trigger == True:

        paths = [os.path.normpath(os.path.join(path_var.get(), f.name)) for f in os.scandir(path_var.get()) if f.is_dir()] # extracts paths from parent folder in proper format
        for path in natsorted(paths): # Natural sorts paths, so that the second path would be "Folder 2", not "Folder 10"
            run_program(path)
        
        message = f"Processed {len(paths) * 429} images in {"%0.6f" % (time.time() - start)} seconds.\nAverage Process Time: {"%0.6f" % ((time.time() - start) / len(paths))} seconds."
        show_message(message)

    else:
        run_program(path_var.get())

        message = f"Processed {429} images in {"%0.6f" % (time.time() - start)} seconds."
        show_message(message)


##########################
#~~~~~~~~~~GUI~~~~~~~~~~~#
##########################

# Create the main window
#root = ctk.CTk()
root.title("Smart Table Plant Image Analysis")
root.minsize(400, 400)
root.resizable(width=False, height=False)

# Create a label and entry to display the selected folder path
path_var = ctk.StringVar()
path_label = ctk.CTkLabel(root, text="Selected Folder Path:")
path_label.pack()
path_entry = ctk.CTkEntry(root, textvariable=path_var, width=300, corner_radius=8)
path_entry.pack()

# Create a button to choose the folder path
choose_button = ctk.CTkButton(master=root, text="Choose Folder", command=choose_folder, width=200, corner_radius=8).place(relx=0.25, rely=0.2)

# Create a button to run the full analysis
run_button = ctk.CTkButton(master=root, text="Run Analysis", command=batch, width=200, corner_radius=8).place(relx=0.25, rely=0.3)

# Create a checkbox to enable batch processing
batch_box = ctk.CTkCheckBox(master=root, text="Enable Batch Processing", command=trigger_batch_status, checkbox_width=30, checkbox_height=30, corner_radius=5)
batch_box.place(relx=0.25, rely=0.4)

# Create a checkbox to enable image saving
save_box = ctk.CTkCheckBox(master=root, text="Enable Image Saving", command=save_image_trigger, checkbox_width=30, checkbox_height=30, corner_radius=5)
save_box.place(relx=0.25, rely=0.5)

# Debug Window Initialization
debug_window = DebugWindow(root)

def clear():
    debug_window.clear()

# This button is only down here because the debug window needs to be intialized
# Along with the clear() method which also requires the debug window to be intialized
clear_debug = ctk.CTkButton(master=root, text="Clear Debug Window", command=clear, width=200, corner_radius=8)
clear_debug.place(relx=0.25, rely=0.6)


def center_window(window):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    #width = window.winfo_width() - 50
    #height = window.winfo_height()
    width = 600
    height = 200
    x = (screen_width + width - 200) // 2
    y = (screen_height + height - 800) // 1
    window.geometry(f"{width}x{height}+{x}+{y}")

# Center debug window when shown
debug_window.bind("<Map>", lambda e: center_window(debug_window))

# Start the Tkinter event loop
root.mainloop()
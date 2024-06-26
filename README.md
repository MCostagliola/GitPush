SMART Table Imaging is a repo which contains a file to install the necessary modules associated with main.py, along with main.py.
To Run the program, first run modules.py, this will download any and all uninstalled required modules.
Do this by runing python .\modules.py in the terminal where the file was downloaded.
From there, run python .\main.py in the terminal where the file was downloaded.
There are two types of processing options:
  Batch Processing & Single Processing
By default the program is set to process single folders, which contain RGB images.
To switch to Batch Processing, just click the "Enable Batch Processing" button in the GUI.
Clicking this button again will disable Batch Processing.
There is also an option to "Enable Image Saving"
The program works by creating a nested folder within the chosen parent folder, which the processed images are then stored in.
From here comparison and anaylsis is done by looping through this folder of processed images.
When processing large datasets, this can quickly eat up space, even though the processed images are roughly 1/3 the file size of the RGB images.
To counteract this, by default, once a folder is processed, it is then deleted.
This applies to both Single and Batch Processing. The processed image folders are deleted before another folder is processed in the case of Batch Processing.
Clicking "Enable Image Saving" will disable the deletion of processed image folders.
If the button is clicked once more, this setting will revert to being disabled.
An Excel File called "MotionSize" will be saved within the folder containing RGB images.

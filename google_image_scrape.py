from pyppeteer import launch
import asyncio
import requests
import os
from os import environ
from tqdm import tqdm
import random
import argparse
import datetime
import threading



async def download(url, pathname):
    number_of_downloads = RUNTIME_STORAGE.number_of_downloads
    attempts = RUNTIME_STORAGE.number_of_download_attempts
    total_download_size = RUNTIME_STORAGE.total_download_size

    attempts = attempts + 1
    RUNTIME_STORAGE.number_of_download_attempts = attempts

    # download the body of response by chunk, not immediately
    response = requests.get(url, stream=True)

    # get the total file size (max of progress bar)
    file_size = int(response.headers.get("Content-Length", 0))

    # get the file name
    file_obj_name = url.split("/")[-1]
    image_extensions = ['.jpg', '.png', '.jpeg']

    if any(extension in url.split("/")[-1] for extension in image_extensions):
        filename = os.path.join(pathname, url.split("/")[-1])
    else:
        print("Garbage------> " + file_obj_name)
        return True
    
    # progress bar, changing the unit to bytes instead of iteration (default by tqdm)
    progress = tqdm(response.iter_content(1024), f"Downloading {file_obj_name}", total=file_size, unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        try:
            for data in progress:
                try:
                    # write data read to the file
                    f.write(data)
                    # update the progress bar manually
                    progress.update(len(data))
                except Exception as e:
                    print("Error downloading: " + url + ", because: " + e)
                    break
        except:
            print('Error downloading image' + file_obj_name)
            pass
        else:
            number_of_downloads = number_of_downloads + 1
            RUNTIME_STORAGE.number_of_downloads = number_of_downloads
            total_download_size = total_download_size + file_size
            RUNTIME_STORAGE.total_download_size = total_download_size
        
        return True

async def load_and_validate_image(thumbnail, page, number_of_files_in_folder, max_number, pathname, delay):
    try:
        # Check if we've reached our maximum number of images in folder
        if number_of_files_in_folder < max_number:

            # click the a tag instead of the parent object
            actual_click = await page.evaluateHandle(
                '(thumbnail) => thumbnail.querySelector("a")',
                thumbnail
            )
            # Click on the thumbnail to expand the full image
            await actual_click.click()

            # Wait for Google to finish serving the image, added variance for fun (if you lower this value, your success rate of downloads will be lower)
            if delay == -1:
                pass
            else:
                random_sleep = random.uniform(delay, delay+0.3)
                await asyncio.sleep(random_sleep)                


            # Get large version of image after clicking on thumbnail
            image_images = await page.querySelectorAll('.n3VNCb')

            # Discard any elements without valid download links, then download
            for item in image_images:
                check = await page.evaluate(
                '(item) => item.src',
                item    
                )
                if 'http' in str(check):
                    pass
                else:
                    continue
                
                # Get rid of the garbage after the .extension in the url 
                image_src = check.split("?")[0]
                
                # Check to make sure it's of one of the extensions I want
                image_extensions = ['.jpg', '.png', '.jpeg']
                if any(extension in str(image_src) for extension in image_extensions):
                    # Download image to save directory
                    await download(image_src, pathname)
    except Exception as e:
        print("Error in download_image(): " + str(e))
        return False

    return True



# Launch a pyppeteer window to navigate to google image search page, then attempt to download max_number of images
async def find_images(search_term, max_number, save_path, delay):
    max = max_number[0]
    print('===============================================================================')
    print('Google Image Scraper v{}'.format(RUNTIME_STORAGE.program_version))
    print('Attempting to download {} pictures of "{}" to {}'.format(max, search_term, save_path))
    print('===============================================================================')
    browser = await launch(
        headless=False,
        args=['--window-size=1200,800'],
        defaultViewport=None
    )
    page = await browser.newPage()
    await page.goto('https://images.google.com')
    await page.type('input[title="Search"]', search_term)
    await page.click('button[type=submit]')
    await page.waitForNavigation()

    # if path doesn't exist, create the save folder
    if not os.path.isdir(save_path):
        os.makedirs(save_path)

    start_time = datetime.datetime.now()
    RUNTIME_STORAGE.start_time = start_time

    # Attempt to download pictures a {max_number} of times, loop asynchronously 
    for num, i in enumerate(range(max-1)):   

        if num % 10 == 0 and num != 0:
            calculate_stats(False)
        # get current thumbnail ElementHandle from persistent local storage
        current_thumbnail = RUNTIME_STORAGE.current_thumbnail
        
        if not current_thumbnail:
            try:
                # This gets the first thumbnail on the page
                current_thumbnail = await page.querySelector('.isv-r.PNCib')
                # current_thumbnail = await page.querySelector('.islrc img.rg_i')
            except:
                # If we can't find it
                raise Exception('Can not find the first thumbnail, quitting')
                break

        try:
            number_of_downloads = RUNTIME_STORAGE.number_of_downloads

            # Create a new parallel task to download the image 
            await asyncio.create_task(load_and_validate_image(current_thumbnail, page, number_of_downloads, max, save_path, delay))
        except Exception as e:
            print("Error finding image: " + str(e))
            break   
        finally:
            # Attempt to find the next thumbnail based on the current element
            try:
                # Get the next thumbnail in the dom, if it's one of Google's "suggested search" thumbnails, skip it
                next_thumbnail = await page.evaluateHandle(
                    '(current_thumbnail) => { \
                        if (current_thumbnail.nextElementSibling.hasAttribute("jsaction")) \
                        { \
                            return current_thumbnail.nextElementSibling; \
                        } \
                        else { \
                            return current_thumbnail.nextElementSibling.nextElementSibling; \
                        } \
                    }',
                    current_thumbnail
                )
                # Set the current thumbnail to the next one in the DOM
                RUNTIME_STORAGE.current_thumbnail = next_thumbnail

            except Exception as e:

                number_of_sequential_errors = RUNTIME_STORAGE.number_of_sequential_errors
                number_of_sequential_errors = number_of_sequential_errors + 1 #
                RUNTIME_STORAGE.number_of_sequential_errors = number_of_sequential_errors

                if "Cannot read property 'hasAttribute' of null" in str(e):
                    print('End of pictures to find, bummer!')
                    break
                print('Error in evaluating the next thumbnail in the DOM' + str(e))
                continue


    calculate_stats(True)
    print("Finished! Closing the browser in 5 seconds...")
    await asyncio.sleep(5000)
    await browser.close()
    

def calculate_stats(show_full_stats):
    # Get final number of images downloaded to save directory
    number_of_downloads = RUNTIME_STORAGE.number_of_downloads
    attempts = RUNTIME_STORAGE.number_of_download_attempts
    success_rate = RUNTIME_STORAGE.success_rate
    start_time = RUNTIME_STORAGE.start_time
    total_download_size = RUNTIME_STORAGE.total_download_size
    total_download_duration = RUNTIME_STORAGE.total_download_duration
    total_calculated_size = RUNTIME_STORAGE.total_calculated_size
    search_term = RUNTIME_STORAGE.search_term
    save_path = RUNTIME_STORAGE.save_path

    # Calculate total size of all images downloaded
    total_size=0.0
    for path, dirs, files in os.walk(save_path):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.path.getsize(fp)
    
    total_calculated_size = total_size

    # Calculate success rate of download attempts
    try:
        decimal_success = round(number_of_downloads/attempts * 100, 2)
        success_rate = str(decimal_success) + "%"
    except ZeroDivisionError as zero_error:
        success_rate = "0%"
        pass

    # Calculate time it took to finish
    now_time = datetime.datetime.now()
    total_seconds = str(round((now_time-start_time).total_seconds(), 1))
    total_download_duration = total_seconds

    # Save back all values to RUNTIME_STORAGE
    RUNTIME_STORAGE.success_rate = success_rate
    RUNTIME_STORAGE.total_download_duration = total_download_duration
    RUNTIME_STORAGE.total_calculated_size = total_calculated_size

    if show_full_stats:
        print('\b===============================================================================')
        print('Search term: {}'.format(search_term))
        print('Download location: {}'.format(save_path))
        print('Total number of successful downloads: {}'.format(number_of_downloads))
        print('Total number of download attempts: {}'.format(attempts))
        print('Download success rate: {}'.format(success_rate))
        print('Total size of all downloads: {} MB'.format(str(round(total_download_size/1000000, 2))))
        print('Total time running: {}'.format(total_download_duration))
        print('===============================================================================\b')
    else:
        print('\b===============================================================================')
        print('Total number of successful downloads: {}'.format(number_of_downloads))
        print('Total number of download attempts: {}'.format(attempts))
        print('Download success rate: {}'.format(success_rate))
        print('Total size of all downloads: {} MB'.format(str(round(total_download_size/1000000, 2))))
        print('Total time running: {} seconds'.format(total_download_duration))
        print('===============================================================================\b')

# Parse command line variables
pictures_default_location = os.path.join(environ["USERPROFILE"], "Pictures")
parser = argparse.ArgumentParser(description="Attempt to download a {max} # of images from Google Images using: {searchterm}; Only supports .jpg, .png, and .jpeg; If you do not include a save location it will default to a new folder in your user's picture folder")
parser.add_argument('--max', metavar='(int)', type=int, nargs='+', help='Max number of images to be downloaded (defaults to 50)')
parser.add_argument('--searchterm', metavar='(string)', type=str, help='Term to search for')
parser.add_argument('--savedir', metavar='(string)', type=str, help="Location to create folder named {searchterm} (if not assigned, defaults to your user's pictures folder")
parser.add_argument('--delay', metavar='(float)', type=float, help="Number of seconds to wait for Google to serve images, if your success rate is low set this to 1.0 or higher (defaults to 0.3)")
args = parser.parse_args()
search_term = args.searchterm
start_time = datetime.datetime.now()

# Check for values else default
if args.max:
    max_number = args.max
else:
    print("no value provided for max number of downloads, defaulting to 100")
    max_number = 100

if args.delay:
    delay = args.delay
else:
    print("no value provided for delay, defaulting to 0.3")
    delay = 0.3

try:
    save_directory = args.savedir
    save_path = os.path.join(save_directory,search_term)
except:
    save_directory = pictures_default_location
    save_path = os.path.join(save_directory,search_term)
# Kick off program here
loop = asyncio.get_event_loop()

# Instantiate RUNTIME_STORAGE, which is persistent local storage outside the asyncio loop
RUNTIME_STORAGE = threading.local()
RUNTIME_STORAGE.current_thumbnail = None
RUNTIME_STORAGE.number_of_downloads = 0
RUNTIME_STORAGE.number_of_download_attempts = 0
RUNTIME_STORAGE.start_time = None
RUNTIME_STORAGE.save_path = save_path
RUNTIME_STORAGE.end_time = None
RUNTIME_STORAGE.success_rate = 0.0
RUNTIME_STORAGE.total_download_size = 0.0
RUNTIME_STORAGE.total_download_duration = 0.0
RUNTIME_STORAGE.total_calculated_size = 0.0
RUNTIME_STORAGE.search_term = search_term
RUNTIME_STORAGE.sequential_errors = 0
RUNTIME_STORAGE.program_version = os.environ.get('VERSION')

try:
    loop.run_until_complete(find_images(search_term, max_number, save_path, delay))  
except KeyboardInterrupt:
    print("Received exit, exiting")
    # find all futures/tasks still running and wait for them to finish
    pending_tasks = [
        task for task in asyncio.Task.all_tasks() if not task.done()
    ]
    print(pending_tasks)
    tasks = loop.run_until_complete(asyncio.gather(*pending_tasks))
    tasks.cancel()
    tasks.exception()
    loop.close()


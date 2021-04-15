# google-image-scrape
Attempt to download a {max} # of pics from Google Images by {searchterm} to the folder {savedir} and iterate through images with a {delay}

Only supports .jpg, .png, and .jpeg, if you do not include {savedir} it will default to a new folder named {searchterm} in your user's picture folder

(requires Python and Pip, https://www.python.org/ftp/python/3.9.4/python-3.9.4-amd64.exe)

STEPS TO SET UP:

1) cd to project folder

2) pipenv install

3) see commands below

**usage:**
   - **google_image_scrape.py --searchterm (string)** --help (help) --max (int) --savedir (string) --delay (float)


**usage examples:**

   - pipenv run python ./google_image_scrape.py --searchterm kittens

   - pipenv run python ./google_image_scrape.py --max 200 --searchterm "happy kittens"

   - pipenv run python ./google_image_scrape.py --max 200 --searchterm "happy kittens" --savedir D:\my_favorite_pictures --delay 1.5

                             
**argument list:**

  -h, --help            show this help message and exit

  --max (int)
                        Max number of images to be downloaded (defaults to 50)
 
  --searchterm (string)
                        Term to search for

  --savedir (string)    Location to create folder named {searchterm} (defaults to your user's pictures folder)

  --delay (float)       Number of seconds to wait for Google to serve images,
                        if your success rate is low set this to 1.0 or higher
                        (defaults to 0.3)

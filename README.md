# google-image-scrape
Attempt to download a {max} # of images from Google Images using: {searchterm} to the folder {savedir}, optionally iterate through images with a {delay}

Only supports .jpg, .png, and .jpeg

If you do not include a save location it will default to a new folder in your user's picture folder

STEPS TO SET UP:

1) cd to project folder

2) pipenv install

3) see commands below

**usage:** google_image_scrape.py -h --max(int) --searchterm(string) --savedir(string) --delay(float)

**usage examples:**

   pipenv run python ./google_image_scrape.py --searchterm kittens

   pipenv run python ./google_image_scrape.py --max 200 --searchterm "happy kittens"

   pipenv run python ./google_image_scrape.py --max 200 --searchterm "happy kittens" --savedir D:\my_favorite_pictures --delay 1.5

                             
**argument list:**

  -h, --help            show this help message and exit

  --max (int) [(int) ...]
                        Max number of images to be downloaded (defaults to 50)

  --searchterm (string)
                        Term to search for

  --savedir (string)    Location to create folder named {searchterm} (if not
                        assigned, defaults to your user's pictures folder

  --delay (float)       Number of seconds to wait for Google to serve images,
                        if your success rate is low set this to 1.0 or higher
                        (defaults to 0.3)

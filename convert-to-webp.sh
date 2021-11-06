#/bin/sh
# Inpiration: http://engineeringblog.yelp.com/2016/05/yelp-android-app-went-on-a-diet.html
# `-lossless` not used to give support for Android 4.0+

# Make sure cwebp is installed.
if ! type "cwebp" > /dev/null; then
    echo "Please install cwebp to continue:"
    echo "brew install webp"
    exit 1
fi

# Convert all the images in the project that are not converted.
for f in $(find . -name "*.jpg")
  do
    echo "Converting $f"
    oldSize=$(du -h $f)
    cwebp -pass 10 -m 6 -mt -jpeg_like -q 60 $f -o "${f/%.jpg/.webp}" &>/dev/null
    newSize=$(du -h ${f/%.jpg/.webp})
    echo "The image was compressed: $oldSize -> $newSize"
    rm $f
done

# Convert all the images in the project that are not converted.
for f in $(find . -name "*.png")
  do
    echo "Converting $f"
    oldSize=$(du -h $f)
    cwebp -pass 10 -m 6 -mt -q 60 $f -o "${f/%.png/.webp}" &>/dev/null
    newSize=$(du -h ${f/%.png/.webp})
    echo "The image was compressed: $oldSize -> $newSize"
    rm $f
done
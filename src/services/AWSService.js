import { getUrl, list } from 'aws-amplify/storage';

export const retrieveImageFromS3 = async (key) => {
    // Key: This converts a str source into a src object for aws to use

    try {
        const res = await list({ prefix: key });
        const urlObj = await getUrl(res.items[0]);
        return urlObj

    } catch (error) {
        console.error("Error retrieving signed URL from S3:", error);
        throw error;
    }
};

export const getFolderContents = async (folderPath) => {
    try {
        const res = await list({ prefix: folderPath });
        return res.Contents
    } catch (err) {
        console.error(err);
    }
};

export const listFoldersInDirectory = async (prefix) => {

    // Ensures that the prefix ends with the specified delimiter
    const delimiter = '/';
    if (prefix && !prefix.endsWith(delimiter)) {
        prefix += delimiter;
    }

    try {
        const data = await list({ prefix: prefix });

        // Extract unique folder names from the current directory
        const uniqueFolders = [];
        const seenFolders = {};

        data.items.forEach(item => {
            const parts = item.key.split(delimiter);
            if (parts.length > 1) {
                const folder = parts[1];
                if (!seenFolders[folder]) {
                    seenFolders[folder] = true;
                    uniqueFolders.push(folder);
                }
            }
        });

        return uniqueFolders;
    } catch (error) {
        throw error;
    }
}

export const listPhotosInFolder = async (folderPath) => {
    const delimiter = '/';

    if (!folderPath.endsWith(delimiter)) {
        folderPath += delimiter;
    }

    try {
        const data = await list({ prefix: folderPath });

        // Filter out folders from the list and return only photo paths
        const photos = data.items
            .filter(object => !object.key.endsWith(delimiter));

        return photos;
    } catch (error) {
        throw error;
    }
};

async function getAspectRatio(imageUrl) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = function () {
            const aspectRatio = img.width / img.height;
            const aspectClass = aspectRatio >= 1 ? 'horizontal' : 'vertical';
            resolve(aspectClass);
        };
        img.onerror = function () {
            reject(new Error('Failed to load image'));
        };
        img.src = imageUrl;
    });
}

export const getPhotoThumbURLAspectClass = async (imgObj) => {
    // This function takes a s3 object and returns the url of the main photo, the thumbnail and the aspect class. This can then be passed to the Photo object

    let full_image_url = null;
    // Load the image from S3 when the component mounts
    await getUrl(imgObj)
        .then((res) => {
            full_image_url = res.url;
        })
        .catch((error) => {
            console.error('Error loading image from S3:', error);
        });


    // TODO: Get the thumbnail url as well
    let thumb_image_url = full_image_url

    // Use the thumb url to determine the aspect class
    const aspectClass = await getAspectRatio(thumb_image_url);

    return [full_image_url, thumb_image_url, aspectClass]
};

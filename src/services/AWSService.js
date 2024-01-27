import { getUrl, list } from 'aws-amplify/storage';

export const retrieveImageFromS3 = async (key) => {
    // Key: This has to be the object from the list() function

    try {
        const url = await getUrl(key, { expiresIn: 30 });
        return url

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
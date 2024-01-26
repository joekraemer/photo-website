import { getUrl, list } from 'aws-amplify/storage';

export const retrieveImageFromS3 = async (key) => {
    // Key: this should be a string like this "recentfavorites/DSC00266.jpg". The bucket gets added here so just the subfolder paths

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

// TODO: this will return more than just folders. I don't know if you can add delimiters with amplify.list
export const listFoldersInDirectory = async (prefix) => {

    // Ensures that the prefix ends with the specified delimiter
    const delimiter = '/';
    if (prefix && !prefix.endsWith(delimiter)) {
        prefix += delimiter;
    }

    try {
        const data = await list({ prefix: prefix });
        return data.CommonPrefixes.map(prefix => prefix.Prefix);
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
        const photoPaths = data.Contents
            .filter(object => !object.Key.endsWith(delimiter))
            .map(object => object.Key);

        return photoPaths;
    } catch (error) {
        throw error;
    }
};
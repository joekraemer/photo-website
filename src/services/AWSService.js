import { GetObjectCommand, S3Client, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner"

const credentials = require('../config/aws-credentials.json');

const s3Client = new S3Client({
    region: 'us-west-1',
    credentials: credentials,
});

export const retrieveImageFromS3 = async (key) => {
    // Key: this should be a string like this "recentfavorites/DSC00266.jpg". The bucket gets added here so just the subfolder paths

    const command = new GetObjectCommand({
        Bucket: 'photo-website-photos',
        Key: key,
    });

    try {
        const url = await getSignedUrl(s3Client, command, { expiresIn: 3600 });
        return url

    } catch (error) {
        console.error("Error retrieving signed URL from S3:", error);
        throw error;
    }
};

export const listBucketContents = async (bucketName) => {
    const command = new ListObjectsV2Command({
        Bucket: bucketName,
        // The default and maximum number of keys returned is 1000. This limits it to
        // one for demonstration purposes.
        MaxKeys: 10,
    });

    try {
        let isTruncated = true;

        console.log("Your bucket contains the following objects:\n");
        let contents = "";

        while (isTruncated) {
            const { Contents, IsTruncated, NextContinuationToken } =
                await s3Client.send(command);
            const contentsList = Contents.map((c) => ` • ${c.Key}`).join("\n");
            contents += contentsList + "\n";
            isTruncated = IsTruncated;
            command.input.ContinuationToken = NextContinuationToken;
        }
        console.log(contents);
    } catch (err) {
        console.error(err);
    }
};

export const getFolderContents = async (bucketName, folderPath) => {
    const command = new ListObjectsV2Command({
        Bucket: bucketName,
        Prefix: folderPath
    });

    try {
        const res = await s3Client.send(command);
        return res.Contents
    } catch (err) {
        console.error(err);
    }
};


export const listFoldersInDirectory = async (bucketName, prefix) => {
    const delimiter = '/';

    if (prefix && !prefix.endsWith(delimiter)) {
        prefix += delimiter;
    }

    const command = new ListObjectsV2Command({
        Bucket: bucketName,
        Prefix: prefix,
        Delimiter: delimiter
    });

    try {
        const data = await s3Client.send(command);
        return data.CommonPrefixes.map(prefix => prefix.Prefix);
    } catch (error) {
        throw error;
    }
}

export const listPhotosInFolder = async (bucketName, folderPath) => {
    const delimiter = '/';

    if (!folderPath.endsWith(delimiter)) {
        folderPath += delimiter;
    }

    const command = new ListObjectsV2Command({
        Bucket: bucketName,
        Prefix: folderPath,
        Delimiter: delimiter
    });

    try {
        const data = await s3Client.send(command);

        // Filter out folders from the list and return only photo paths
        const photoPaths = data.Contents
            .filter(object => !object.Key.endsWith(delimiter))
            .map(object => object.Key);

        return photoPaths;
    } catch (error) {
        throw error;
    }
};
import { GetObjectCommand, S3Client, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner"

const s3Client = new S3Client({
    region: 'us-west-1',
    credentials: CREDENTIAL,
});

export const retrieveImageFromS3 = async (key) => {
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

export const getBucketContents = async (bucketName) => {
    const command = new ListObjectsV2Command({
        Bucket: bucketName,
        // The default and maximum number of keys returned is 1000. This limits it to
        // one for demonstration purposes.
        MaxKeys: 10,
    });

    try {
        const res = await s3Client.send(command);
        return res.Contents
    } catch (err) {
        console.error(err);
    }
};

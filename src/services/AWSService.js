import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";

const s3Client = new S3Client({});

export const retrieveImageFromS3 = async (key) => {
    const command = new GetObjectCommand({
        Bucket: 'photo-website-photos',
        Key: key,
    });

    try {
        const response = await s3Client.send(command);
        const imageContent = await response.Body.transformToBlob();
        return imageContent;
    } catch (error) {
        console.error("Error retrieving image from S3:", error);
        throw error;
    }
};

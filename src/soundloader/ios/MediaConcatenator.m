//
//  MediaConcatenator.m
//  SoundLoader
//
//  Created by Max Green on 10/5/25.
//

#import "MediaConcatenator.h"
#import <AVFoundation/AVFoundation.h>
#import <CoreMedia/CoreMedia.h>
#import <AVFoundation/AVMediaFormat.h>

@implementation MediaConcatenator

- (void)concatenateAudioFiles:(NSArray<NSURL *> *)fileURLs
                  toOutputURL:(NSURL *)outputURL
            completionHandler:(void (^)(BOOL success, NSError * _Nullable error))completionHandler
{
    // 1. Setup the Composition and Track
    AVMutableComposition *composition = [AVMutableComposition composition];
    AVMutableCompositionTrack *audioTrack = [composition addMutableTrackWithMediaType:AVMediaTypeAudio
                                                                     preferredTrackID:kCMPersistentTrackID_Invalid];

    CMTime currentTime = kCMTimeZero;
    NSError *error = nil;

    // 2. Insert each file's audio track into the composition
    for (NSURL *fileURL in fileURLs) {
        AVURLAsset *asset = [AVURLAsset URLAssetWithURL:fileURL options:nil];
        AVAssetTrack *sourceTrack = [[asset tracksWithMediaType:AVMediaTypeAudio] firstObject];

        if (sourceTrack) {
            CMTimeRange timeRange = sourceTrack.timeRange;
            
            BOOL success = [audioTrack insertTimeRange:timeRange
                                               ofTrack:sourceTrack
                                                atTime:currentTime
                                                 error:&error];

            if (!success || error) {
                // Fail fast if an insertion fails
                completionHandler(NO, error);
                return;
            }

            // Move the insertion point to the end of the newly added track
            currentTime = composition.duration;
        }
    }

    // 3. Setup Export Session
    [[NSFileManager defaultManager] removeItemAtURL:outputURL error:nil];
    
    // Using AVAssetExportPresetAppleM4A is standard for high-quality audio export
    AVAssetExportSession *exporter = [[AVAssetExportSession alloc] initWithAsset:composition
                                                                       presetName:AVAssetExportPresetAppleM4A];
    exporter.outputURL = outputURL;
    exporter.outputFileType = AVFileTypeMPEGLayer3;
    
    // 4. Perform Export Asynchronously
    [exporter exportAsynchronouslyWithCompletionHandler:^{
        // Use the main queue for the completion handler, as is common practice
        dispatch_async(dispatch_get_main_queue(), ^{
            switch (exporter.status) {
                case AVAssetExportSessionStatusCompleted:
                    completionHandler(YES, nil);
                    break;
                case AVAssetExportSessionStatusFailed:
                    completionHandler(NO, exporter.error);
                    break;
                case AVAssetExportSessionStatusCancelled:
                    // Treat cancellation as a failure, or handle separately if desired
                    completionHandler(NO, nil);
                    break;
                default:
                    // In-progress, waiting, or unknown
                    break;
            }
        });
    }];
}

@end

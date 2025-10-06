// MediaConcatenator.h
#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface MediaConcatenator : NSObject

/**
 * Concatenates a list of audio file URLs into a single output file.
 *
 * @param fileURLs An array of NSURL objects pointing to the source audio files.
 * @param outputURL The NSURL where the final merged audio file will be saved.
 * @param completionHandler A block to be executed when the export is complete.
 * The 'success' BOOL indicates the outcome.
 */
- (void)concatenateAudioFiles:(NSArray<NSURL *> *)fileURLs
                  toOutputURL:(NSURL *)outputURL
            completionHandler:(void (^)(BOOL success, NSError * _Nullable error))completionHandler;

@end

NS_ASSUME_NONNULL_END

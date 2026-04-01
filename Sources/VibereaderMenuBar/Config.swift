import Foundation

enum Config {
    static var apiURL: String {
        ProcessInfo.processInfo.environment["VIBEREADER_API"] ?? "http://localhost:8888"
    }
}

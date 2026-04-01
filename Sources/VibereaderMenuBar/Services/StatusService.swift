import Foundation
import os.log

final class StatusService {
    private let logger = Logger(subsystem: "com.vibereader.menubar", category: "StatusService")

    func fetchStatus() async throws -> ClaudeStatus {
        guard let url = URL(string: "\(Config.apiURL)/api/status") else {
            throw URLError(.badURL)
        }
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(ClaudeStatus.self, from: data)
    }
}

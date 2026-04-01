import Foundation

struct ClaudeStatus: Decodable {
    let claudeActive: Bool
    let idleSeconds: Int
    let toolCallCount: Int

    enum CodingKeys: String, CodingKey {
        case claudeActive = "claude_active"
        case idleSeconds = "idle_seconds"
        case toolCallCount = "tool_call_count"
    }
}

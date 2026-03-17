-- Example Lua Script for Veus
-- This script responds with "pong" when it sees "!ping"

success("Example script loaded!")

register_hook("MESSAGE_CREATE", function(data)
    local content = data.content
    local channel_id = data.channel_id
    local author = data.author.username

    if content == "!ping" then
        info("Ping detected from " .. author)
        send_message(channel_id, "pong! (responding from Lua)")
    end
end)

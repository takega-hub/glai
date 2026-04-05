import React, { useState, useEffect, useCallback } from "react";
import { GiftedChat } from "react-native-gifted-chat";
import chatService from "../services/chatService";

const ChatScreen = ({ route }) => {
  const { characterId } = route.params;
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    try {
      const history = await chatService.getChatHistory(characterId);
      const formattedMessages = history.map((msg) => ({
        _id: msg.id,
        text: msg.response || msg.message,
        createdAt: new Date(msg.created_at),
        user: {
          _id: msg.message ? 1 : 2, // 1 for user, 2 for character
          name: msg.message ? "User" : "Character",
        },
        image: msg.image_url,
      }));
      setMessages(formattedMessages.reverse());
    } catch (error) {
      console.error("Failed to load chat history:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [characterId]);

  const onSend = useCallback(async (newMessages = []) => {
    const messageText = newMessages[0].text;
    setMessages((previousMessages) =>
      GiftedChat.append(previousMessages, newMessages)
    );

    try {
      await chatService.sendMessage(characterId, messageText);
      // After sending, reload the history to get the response
      await loadHistory();
    } catch (error) {
      console.error("Failed to send message:", error);
      // Optionally, show an error message to the user
    }
  }, [characterId]);

  return (
    <GiftedChat
      messages={messages}
      onSend={(msgs) => onSend(msgs)}
      user={{
        _id: 1,
      }}
      isLoadingEarlier={loading}
    />
  );
};

export default ChatScreen;

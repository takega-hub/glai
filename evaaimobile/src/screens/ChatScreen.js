import React, { useState, useEffect, useCallback } from "react";
import { View, StyleSheet, ActivityIndicator, Text, TouchableOpacity } from "react-native";
import { GiftedChat, Bubble, Send, InputToolbar } from "react-native-gifted-chat";
import { launchImageLibrary } from "react-native-image-picker";
import { useAuthStore } from "../store/authStore";
import chatService from "../services/chatService";
import { Gift, Image as ImageIcon } from "lucide-react-native";

const ChatScreen = ({ route, navigation }) => {
  const { characterId, characterName } = route.params;
  const { user, updateBalance } = useAuthStore();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    navigation.setOptions({ title: characterName });
  }, [characterName, navigation]);

  const loadChat = useCallback(async () => {
    try {
      const history = await chatService.getChatHistory(characterId);
      const formattedMessages = history.map((msg) => ({
        _id: msg.id,
        text: msg.response || msg.message,
        createdAt: new Date(msg.created_at),
        user: {
          _id: msg.message ? 1 : 2, 
        },
        image: msg.image_url,
        system: msg.sender === "system",
      }));
      setMessages(formattedMessages.reverse());
    } catch (error) {
      console.error("Failed to load chat history:", error);
    } finally {
      setLoading(false);
    }
  }, [characterId]);

  useEffect(() => {
    loadChat();
  }, [loadChat]);

  const onSend = useCallback(async (newMessages = []) => {
    const { text, image } = newMessages[0];
    setMessages((previousMessages) =>
      GiftedChat.append(previousMessages, newMessages)
    );

    try {
      await chatService.sendMessage(characterId, text, image);
      const balanceData = await chatService.getBalance();
      updateBalance(balanceData.balance);
      await loadChat();
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  }, [characterId, loadChat, updateBalance]);

  const handlePickImage = () => {
    launchImageLibrary({ mediaType: "photo" }, (response) => {
      if (response.didCancel) return;
      if (response.errorCode) {
        console.log("ImagePicker Error: ", response.errorMessage);
        return;
      }
      if (response.assets && response.assets[0]) {
        const asset = response.assets[0];
        const imageMessage = {
          _id: Math.random().toString(36).substring(7),
          createdAt: new Date(),
          user: { _id: 1 },
          image: asset.uri,
          // Pass the full asset to onSend to be handled by sendMessage service
          asset: asset 
        };
        onSend([imageMessage]);
      }
    });
  };

  const renderBubble = (props) => (
    <Bubble
      {...props}
      wrapperStyle={{
        right: { backgroundColor: "#6B21A8" },
        left: { backgroundColor: "#1F2937" },
      }}
      textStyle={{ right: { color: "#FFF" }, left: { color: "#FFF" } }}
    />
  );

  const renderInputToolbar = (props) => (
    <InputToolbar
      {...props}
      containerStyle={{ backgroundColor: "#111827", borderTopColor: "#374151" }}
      primaryStyle={{ alignItems: "center" }}
    />
  );

  const renderActions = (props) => (
    <View style={{ flexDirection: "row" }}>
      <TouchableOpacity style={styles.actionButton} onPress={handlePickImage}>
        <ImageIcon color="#9CA3AF" size={24} />
      </TouchableOpacity>
    </View>
  );

  const renderSend = (props) => (
    <Send {...props} containerStyle={{ justifyContent: "center" }}>
      <Text style={{ color: "#8B5CF6", marginRight: 10, fontWeight: "bold" }}>Send</Text>
    </Send>
  );

  if (loading) {
    return <ActivityIndicator size="large" style={{ flex: 1 }} />;
  }

  return (
    <GiftedChat
      messages={messages}
      onSend={onSend}
      user={{ _id: 1 }}
      renderBubble={renderBubble}
      renderInputToolbar={renderInputToolbar}
      renderActions={renderActions}
      renderSend={renderSend}
      alwaysShowSend
      placeholder="Type a message..."
      textInputStyle={{ color: "#FFF" }}
    />
  );
};

const styles = StyleSheet.create({
  actionButton: {
    padding: 10,
  },
});

export default ChatScreen;

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  View,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  Alert,
  StatusBar,
} from "react-native";
import { GiftedChat, Bubble, Send, InputToolbar, Actions, Message } from "react-native-gifted-chat";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { launchImageLibrary } from "react-native-image-picker";
import { useAuthStore } from "../store/authStore";
import chatService from "../services/chatService";
import { Gift as GiftIcon, Send as SendIcon, Plus } from "lucide-react-native";
import GiftModal from "../components/GiftModal";

const ChatScreen = ({ route, navigation }) => {
  const { characterId, characterName } = route.params;
  const insets = useSafeAreaInsets();
  const updateBalance = useAuthStore((state) => state.user ? state.updateBalance : () => {});
  const balance = useAuthStore((state) => state.balance);

  const [messages, setMessages] = useState([]);
  const messagesRef = useRef([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  const [loading, setLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [isGiftModalOpen, setIsGiftModalOpen] = useState(false);

  useEffect(() => {
    navigation.setOptions({
      title: characterName,
      headerStyle: { backgroundColor: "#1e1b4b" },
      headerTintColor: "#fff",
    });
  }, [characterName, navigation]);

  const formatHistory = useCallback((history) => {
    const getFullImageUrl = (url) => {
      if (!url) return null;
      return url.startsWith("http") ? url : `https://eva.midoma.ru${url}`;
    };

    return history.map((msg, index) => {
      // 1. Создаем стабильный ID. Если нет msg.id, используем комбинацию роли и времени
      const stableId = msg.id || `${msg.role}-${msg.created_at || index}`;

      // 2. Очистка контента от логов OpenRouter
      let cleanContent = msg.content || "";
      if (cleanContent.includes("--- RECEIVED RESPONSE FROM OPENROUTER ---")) {
        try {
          // Если пришел лог, пытаемся вытащить только текст из JSON внутри лога
          const parts = cleanContent.split("--- RECEIVED RESPONSE FROM OPENROUTER ---");
          const jsonStr = parts[parts.length - 1].trim();
          if (jsonStr.startsWith("{")) {
            const parsed = JSON.parse(jsonStr);
            cleanContent = parsed.choices?.[0]?.message?.content || cleanContent;
          } else {
            cleanContent = jsonStr;
          }
        } catch (e) {
          // Если не распарсилось, просто берем часть после разделителя
          const parts = cleanContent.split("--- RECEIVED RESPONSE FROM OPENROUTER ---");
          cleanContent = parts[parts.length - 1].trim();
        }
      }

      return {
        _id: stableId,
        text: cleanContent,
        createdAt: new Date(msg.created_at || Date.now()),
        user: {
          _id: msg.role === "user" ? 1 : 2,
          name: msg.role === "user" ? "Me" : characterName,
        },
        image: getFullImageUrl(msg.image_url),
      };
    });
  }, [characterName]);

  const loadChat = useCallback(async (isInitialLoad = false) => {
    if (isInitialLoad) setLoading(true);
    try {
      const history = await chatService.getChatHistory(characterId);
      if (Array.isArray(history)) {
        const formatted = formatHistory(history);
        setMessages(formatted.reverse());
      }
    } catch (error) {
      console.error("Failed to load chat history:", error);
    } finally {
      if (isInitialLoad) setLoading(false);
    }
  }, [characterId, formatHistory]);

  useEffect(() => {
    loadChat(true);
  }, [loadChat]);

  const delay = (ms) => new Promise(res => setTimeout(res, ms));

  const onSend = useCallback(
    async (newMessages = []) => {
      const { text, image } = newMessages[0];
      setMessages((previousMessages) => GiftedChat.append(previousMessages, newMessages));
      setIsTyping(true);

      try {
        await chatService.sendMessage(characterId, text, image);
        const updatedHistory = await chatService.getChatHistory(characterId);

        if (Array.isArray(updatedHistory)) {
          const formattedAll = formatHistory(updatedHistory).reverse();
          // Используем ref для получения актуального списка ID
          const currentIds = new Set(messagesRef.current.map(m => m._id));
          const newBotMessages = formattedAll.filter(m => m.user._id === 2 && !currentIds.has(m._id)).reverse();

          for (const botMsg of newBotMessages) {
            setIsTyping(true);
            const typingSpeed = Math.min(Math.max(botMsg.text.length * 50, 1000), 3000);
            await delay(typingSpeed);
            setMessages((prev) => GiftedChat.append(prev, [botMsg]));
            setIsTyping(false);
            await delay(500);
          }
        }

        const balanceData = await chatService.getBalance();
        if (balanceData?.balance !== undefined) updateBalance(balanceData.balance);
      } catch (error) {
        console.error("Failed to send message:", error);
        setIsTyping(false);
      } finally {
        setIsTyping(false);
      }
    },
    [characterId, formatHistory, updateBalance]
  );

  const handlePickImage = () => {
    launchImageLibrary({ mediaType: "photo", quality: 0.8 }, (response) => {
      if (response.assets?.[0]) {
        const asset = response.assets[0];
        onSend([{
          _id: Math.random().toString(36),
          createdAt: new Date(),
          user: { _id: 1 },
          image: asset.uri,
          text: "",
        }]);
      }
    });
  };

  const handleSendGift = async (giftType) => {
    try {
      await chatService.sendGift(characterId, giftType);
      setIsGiftModalOpen(false);
      const balanceData = await chatService.getBalance();
      if (balanceData?.balance !== undefined) updateBalance(balanceData.balance);
      Alert.alert("Success", `Gift sent to ${characterName}!`);
      loadChat();
    } catch (error) {
      Alert.alert("Error", "Check your balance.");
    }
  };

  const renderBubble = (props) => (
    <Bubble
      {...props}
      wrapperStyle={{
        right: { backgroundColor: "#a855f7", borderRadius: 18, padding: 2 },
        left: { backgroundColor: "rgba(255, 255, 255, 0.1)", borderRadius: 18, padding: 2 },
      }}
      textStyle={{ right: { color: "white" }, left: { color: "white" } }}
    />
  );

  const renderInputToolbar = (props) => (
    <InputToolbar
      {...props}
      containerStyle={styles.inputToolbar}
      primaryStyle={{ alignItems: "center" }}
    />
  );

  const renderActions = (props) => (
    <View style={styles.actionsRow}>
      <Actions
        {...props}
        containerStyle={styles.actionsContainer}
        icon={() => <Plus size={24} color="#d8b4fe" />}
        onPressActionButton={handlePickImage}
      />
      <TouchableOpacity style={styles.giftIconButton} onPress={() => setIsGiftModalOpen(true)}>
        <GiftIcon size={24} color="#d8b4fe" />
      </TouchableOpacity>
    </View>
  );

  const renderSend = (props) => (
    <Send {...props} containerStyle={styles.sendContainer}>
      <View style={styles.sendButton}>
        <SendIcon size={20} color="white" />
      </View>
    </Send>
  );

  const renderMessage = (msgProps) => {
    return <Message {...msgProps} key={msgProps.currentMessage._id} />;
  };

  return (
    <View style={[styles.container, { paddingBottom: insets.bottom }]}>
      <StatusBar barStyle="light-content" />
      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#a855f7" />
        </View>
      ) : (
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 100}
        >
          <GiftedChat
            messages={messages}
            onSend={onSend}
            user={{ _id: 1 }}
            renderBubble={renderBubble}
            renderInputToolbar={renderInputToolbar}
            renderActions={renderActions}
            renderSend={renderSend}
            renderMessage={renderMessage}
            alwaysShowSend
            isTyping={isTyping}
            placeholder="Type a message..."
            textInputStyle={styles.textInput}
            renderUsernameOnMessage={false}
            showUserAvatar={false}
            maxInputLength={500}
            bottomOffset={0}
            minInputToolbarHeight={64}
            keyboardShouldPersistTaps="handled"
          />
        </KeyboardAvoidingView>
      )}

      <GiftModal
        isOpen={isGiftModalOpen}
        onClose={() => setIsGiftModalOpen(false)}
        onSendGift={handleSendGift}
        currentTokenBalance={balance}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#0f172a",
  },
  inputToolbar: {
    backgroundColor: "rgba(30, 41, 59, 1)",
    borderTopWidth: 1,
    borderTopColor: "rgba(255, 255, 255, 0.1)",
    marginHorizontal: 0,
    borderRadius: 0,
    paddingHorizontal: 4,
  },
  textInput: {
    color: "white",
    fontSize: 16,
    paddingTop: 8,
  },
  actionsRow: {
    flexDirection: "row",
    alignItems: "center",
    marginLeft: 4,
  },
  actionsContainer: {
    width: 32,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  giftIconButton: {
    width: 32,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  sendContainer: {
    width: 44,
    height: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  sendButton: {
    backgroundColor: "#a855f7",
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default ChatScreen;

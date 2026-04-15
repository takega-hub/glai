import React from "react";
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
} from "react-native";
import { X, Gift, Star, Zap } from "lucide-react-native";

const GIFTS = [
  { name: "Small Gift", type: "small", cost: 10, points: 10, icon: Gift },
  { name: "Medium Gift", type: "medium", cost: 25, points: 30, icon: Star },
  { name: "Large Gift", type: "large", cost: 50, points: 75, icon: Zap },
];

const GiftModal = ({ isOpen, onClose, onSendGift, currentTokenBalance }) => {
  if (!isOpen) return null;

  return (
    <Modal
      animationType="fade"
      transparent={true}
      visible={isOpen}
      onRequestClose={onClose}
    >
      <Pressable style={styles.overlay} onPress={onClose}>
        <Pressable style={styles.modalContainer} onPress={(e) => e.stopPropagation()}>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <X size={24} color="#d8b4fe" />
          </TouchableOpacity>

          <Text style={styles.title}>Send a Gift</Text>
          <Text style={styles.subtitle}>
            Increase your trust level by sending a gift!
          </Text>

          <View style={styles.giftList}>
            {GIFTS.map((gift) => {
              const canAfford = currentTokenBalance >= gift.cost;
              const Icon = gift.icon;

              return (
                <TouchableOpacity
                  key={gift.type}
                  style={[
                    styles.giftItem,
                    !canAfford && styles.giftItemDisabled,
                  ]}
                  onPress={() => canAfford && onSendGift(gift.type)}
                  disabled={!canAfford}
                >
                  <View style={styles.giftInfo}>
                    <View style={styles.iconContainer}>
                      <Icon size={24} color="#e9d5ff" />
                    </View>
                    <View style={styles.textContainer}>
                      <Text style={styles.giftName}>{gift.name}</Text>
                      <Text style={styles.pointsText}>+{gift.points} to trust</Text>
                    </View>
                  </View>
                  <View style={styles.costContainer}>
                    <Text style={styles.costValue}>{gift.cost}</Text>
                    <Text style={styles.costLabel}>tokens</Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>

          <View style={styles.balanceContainer}>
            <Text style={styles.balanceText}>
              Your balance: <Text style={styles.balanceValue}>{currentTokenBalance}</Text> tokens
            </Text>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  modalContainer: {
    backgroundColor: "rgba(30, 27, 75, 0.95)", // Deep indigo with high opacity for readability
    borderRadius: 24,
    padding: 24,
    width: "100%",
    maxWidth: 400,
    borderWidth: 1,
    borderColor: "rgba(168, 85, 247, 0.4)", // Purple-500 with opacity
    shadowColor: "#a855f7",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  closeButton: {
    position: "absolute",
    top: 16,
    right: 16,
    zIndex: 10,
    backgroundColor: "rgba(255, 255, 255, 0.05)",
    borderRadius: 12,
    padding: 4,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "white",
    textAlign: "center",
    marginBottom: 4,
    textShadowColor: "rgba(168, 85, 247, 0.5)",
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#d8b4fe", // purple-300
    textAlign: "center",
    marginBottom: 24,
  },
  giftList: {
    gap: 12,
  },
  giftItem: {
    backgroundColor: "rgba(255, 255, 255, 0.03)",
    borderRadius: 16,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.08)",
  },
  giftItemDisabled: {
    opacity: 0.5,
  },
  giftInfo: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  iconContainer: {
    backgroundColor: "rgba(168, 85, 247, 0.2)", // purple-500/20
    padding: 12,
    borderRadius: 12,
  },
  textContainer: {
    justifyContent: "center",
  },
  giftName: {
    fontSize: 18,
    fontWeight: "bold",
    color: "white",
  },
  pointsText: {
    fontSize: 14,
    color: "#4ade80", // green-400
  },
  costContainer: {
    alignItems: "flex-end",
  },
  costValue: {
    fontSize: 18,
    fontWeight: "bold",
    color: "white",
  },
  costLabel: {
    fontSize: 12,
    color: "#d8b4fe",
  },
  balanceContainer: {
    marginTop: 24,
    alignItems: "center",
  },
  balanceText: {
    color: "#e9d5ff",
    fontSize: 16,
  },
  balanceValue: {
    fontWeight: "bold",
    color: "white",
  },
});

export default GiftModal;

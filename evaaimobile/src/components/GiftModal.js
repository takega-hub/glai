import React from "react";
import { Modal, View, Text, StyleSheet, Button, TouchableOpacity } from "react-native";

const GIFTS = [
  { type: "small", name: "Small Gift", cost: 50 },
  { type: "medium", name: "Medium Gift", cost: 150 },
  { type: "large", name: "Large Gift", cost: 300 },
];

const GiftModal = ({ isOpen, onClose, onSendGift, currentTokenBalance }) => {
  return (
    <Modal
      animationType="slide"
      transparent={true}
      visible={isOpen}
      onRequestClose={onClose}
    >
      <View style={styles.centeredView}>
        <View style={styles.modalView}>
          <Text style={styles.modalText}>Send a Gift</Text>
          <Text style={styles.balanceText}>Your balance: {currentTokenBalance} tokens</Text>
          
          {GIFTS.map((gift) => (
            <TouchableOpacity 
              key={gift.type} 
              style={styles.giftButton} 
              onPress={() => onSendGift(gift.type)}
              disabled={currentTokenBalance < gift.cost}
            >
              <Text style={styles.giftButtonText}>{gift.name} ({gift.cost} tokens)</Text>
            </TouchableOpacity>
          ))}

          <Button title="Close" onPress={onClose} />
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  centeredView: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.5)",
  },
  modalView: {
    margin: 20,
    backgroundColor: "white",
    borderRadius: 20,
    padding: 35,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 2
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5
  },
  modalText: {
    marginBottom: 15,
    textAlign: "center",
    fontSize: 20,
    fontWeight: "bold",
  },
  balanceText: {
    marginBottom: 20,
    fontSize: 16,
  },
  giftButton: {
    backgroundColor: "#6B21A8",
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    width: 200,
    alignItems: "center",
  },
  giftButtonText: {
    color: "white",
    fontWeight: "bold",
  },
});

export default GiftModal;

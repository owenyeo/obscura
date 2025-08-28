// App.tsx
import { useState } from "react";
import { Image, View, Text, Pressable, ActivityIndicator, StyleSheet } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { Platform } from "react-native";
import * as FileSystem from "expo-file-system"; // native only

const API = "http://localhost:8080/analyze/image";

export default function App() {
  const [img, setImg] = useState<{ uri: string; type?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function pick() {
    setErr(null);
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") return setErr("Permission denied");
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
      allowsMultipleSelection: false,
    });
    if (!res.canceled) {
      const a = res.assets[0];
      setImg({ uri: a.uri, type: a.mimeType ?? "image/jpeg" });
    }
  }

  
  async function upload(img: { uri: string; type?: string }) {
    if (!img) return;

    if (Platform.OS === "web") {
      // WEB: turn the picked URI into a Blob, then send FormData
      const resp = await fetch(img.uri);
      const blob = await resp.blob();

      const fd = new FormData();
      fd.append("file", blob, "photo.jpg");     // proper file field
      // fd.append("modes", "ocr,face");        // optional extra fields

      const r = await fetch(API, { method: "POST", body: fd }); // don't set Content-Type
      if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
      return r.json();
    } else {
      // NATIVE (iOS/Android): use FileSystem helper or FormData {uri,name,type}
      // A) Robust streaming upload:
      const res = await FileSystem.uploadAsync(API, img.uri, {
        httpMethod: "POST",
        uploadType: FileSystem.FileSystemUploadType.MULTIPART,
        fieldName: "file",
        mimeType: img.type || "image/jpeg",
        // parameters: { modes: "ocr,face" },   // optional
      });
      if (res.status !== 200) throw new Error(`${res.status} ${res.body}`);
      return JSON.parse(res.body);
    }
  }

  return (
    <View style={{ padding: 16, gap: 12, flex: 1, justifyContent: "center"}}>
      <UploadBox
        imageUri={img?.uri || null}
        busy={busy}
        onPress={pick}
      />

      {img && (
        <Pressable
          onPress={upload}
          disabled={busy}
          style={[styles.uploadBtn, busy && { opacity: 0.6 }]}
          accessibilityRole="button"
        >
          <Text style={styles.uploadBtnText}>{busy ? "Uploading…" : "Upload"}</Text>
        </Pressable>
      )}

      {err && <Text style={{ color: "red" }}>{err}</Text>}
    </View>
  );
}

function UploadBox({
  imageUri,
  onPress,
  busy,
}: {
  imageUri: string | null;
  onPress: () => void;
  busy?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.box,
        pressed && { opacity: 0.85 },
        imageUri ? styles.boxWithImage : styles.boxEmpty,
      ]}
    >
      {imageUri ? (
        <>
          <Image source={{ uri: imageUri }} style={styles.boxImage} resizeMode="contain"/>
          <View style={styles.overlay}>
            <Text style={styles.overlayText}>{busy ? "Busy…" : "Tap to change"}</Text>
          </View>
        </>
      ) : (
        <View style={styles.boxInner}>
          <Text style={styles.icon}>⬆️</Text>
          <Text style={styles.title}>Tap to upload</Text>
          <Text style={styles.subtitle}>PNG or JPG, up to ~10MB</Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  box: {
    flex: 1,             // take available vertical space
    width: "100%",
    borderRadius: 12,
    overflow: "hidden",
  },
  boxEmpty: {
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#BDBDBD",
    backgroundColor: "#FAFAFA",
    alignItems: "center",
    justifyContent: "center",
  },
  boxWithImage: {
    borderWidth: 0,
    backgroundColor: "#000",
  },
  boxInner: { alignItems: "center", gap: 6 },
  icon: { fontSize: 28, marginBottom: 4 },
  title: { fontSize: 16, fontWeight: "600" },
  subtitle: { fontSize: 12, color: "#666" },
  boxImage: { width: "100%", height: "100%" },
  overlay: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    paddingVertical: 8,
    backgroundColor: "rgba(0,0,0,0.4)",
    alignItems: "center",
  },
  overlayText: { color: "#fff", fontWeight: "600" },
  uploadBtn: {
    backgroundColor: "#111",
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  uploadBtnText: { color: "#fff", fontWeight: "600" },
});

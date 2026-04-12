interface AppleIDAuth {
  signIn: () => Promise<any>;
}

declare global {
  interface Window {
    AppleID: {
      auth: AppleIDAuth;
    };
  }
}

export {};

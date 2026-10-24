const SECRETOS =
  /\.env(\..*)?$|\.(pem|key|p12|pfx|jks|keystore)$|id_rsa|credentials|service-account.*\.json|\.tfvars$/i

export const ProteccionSecretos = async () => ({
  "tool.execute.before": async (input, output) => {
    const ruta = output?.args?.filePath ?? output?.args?.command ?? ""
    if ((input.tool === "read" || input.tool === "bash") && SECRETOS.test(ruta)) {
      throw new Error("Bloqueado por política del workspace: posible archivo de secretos.")
    }
  },
})

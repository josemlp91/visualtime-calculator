export interface AuthResponse {
    user: {
        id: number,
        idCompany: number,
        companyName: string,
        displayName: string,
        username: string,
        isSupervisor: false,
        password: string,
        validationCode: string,
        validationCodeStamp: Date,
        token: string
    }
}
